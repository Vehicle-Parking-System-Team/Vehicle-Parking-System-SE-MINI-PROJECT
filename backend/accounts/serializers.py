from django.contrib.auth import authenticate
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    """Public profile representation for authenticated users."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'status']
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    """Validates user credentials and produces JWT token pair with user context."""

    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        username = attrs.get('username', '').strip()
        password = attrs.get('password', '')

        if not username or not password:
            raise serializers.ValidationError({
                'non_field_errors': ['Must include both username and password.']
            })

        user = authenticate(username=username, password=password)

        if not user:
            # Generic message prevents leaking whether the username exists
            raise exceptions.AuthenticationFailed('Invalid username or password.')

        if not user.is_active or user.status != 'active':
            raise exceptions.AuthenticationFailed('User account is inactive or suspended.')

        # Generate tokens with embedded claims
        refresh = RefreshToken.for_user(user)
        refresh['token_version'] = user.token_version
        refresh['role'] = user.role
        refresh['username'] = user.username

        access = refresh.access_token
        access['token_version'] = user.token_version
        access['role'] = user.role
        access['username'] = user.username

        return {
            'access': str(access),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        }


class LogoutSerializer(serializers.Serializer):
    """Validates refresh token to be blacklisted upon logout."""

    refresh = serializers.CharField(required=True)


class CustomTokenRefreshSerializer(serializers.Serializer):
    """Refreshes an access token while verifying account status and token revocation."""

    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        refresh_str = attrs.get('refresh')

        try:
            refresh = RefreshToken(refresh_str)
        except TokenError:
            raise exceptions.AuthenticationFailed('Token is invalid or expired.')

        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        try:
            user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found.')

        if not user.is_active or user.status != 'active':
            raise exceptions.AuthenticationFailed('User account is inactive or suspended.')

        token_version = refresh.payload.get('token_version')
        if token_version is not None and token_version != user.token_version:
            raise exceptions.AuthenticationFailed('Token has been revoked.')

        # Blacklist old refresh token and rotate to a new one
        try:
            refresh.blacklist()
        except TokenError:
            raise exceptions.AuthenticationFailed('Token is invalid or expired.')

        new_refresh = RefreshToken.for_user(user)
        new_refresh['token_version'] = user.token_version
        new_refresh['role'] = user.role
        new_refresh['username'] = user.username

        new_access = new_refresh.access_token
        new_access['token_version'] = user.token_version
        new_access['role'] = user.role
        new_access['username'] = user.username

        return {
            'access': str(new_access),
            'refresh': str(new_refresh),
        }
