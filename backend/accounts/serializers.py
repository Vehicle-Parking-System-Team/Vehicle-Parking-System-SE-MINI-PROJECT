import re
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User


def validate_password_policy(password, user=None):
    """
    Enforces password complexity per SAD §5.1:
    >= 8 chars, >= 1 uppercase, >= 1 lowercase, >= 1 digit, >= 1 special character.
    """
    if len(password) < 8:
        raise serializers.ValidationError({
            'password': ['Password must be at least 8 characters long.']
        })
    if not re.search(r'[A-Z]', password):
        raise serializers.ValidationError({
            'password': ['Password must contain at least one uppercase letter.']
        })
    if not re.search(r'[a-z]', password):
        raise serializers.ValidationError({
            'password': ['Password must contain at least one lowercase letter.']
        })
    if not re.search(r'[0-9]', password):
        raise serializers.ValidationError({
            'password': ['Password must contain at least one digit.']
        })
    if not re.search(r'[^A-Za-z0-9]', password):
        raise serializers.ValidationError({
            'password': ['Password must contain at least one special character.']
        })
    try:
        validate_password(password, user=user)
    except DjangoValidationError as e:
        raise serializers.ValidationError({'password': list(e.messages)})


class UserSerializer(serializers.ModelSerializer):
    """Public profile representation for authenticated users (US-01, US-02, US-04)."""

    contact_number = serializers.CharField(source='phone_number', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'contact_number', 'role', 'status',
        ]
        read_only_fields = fields


def validate_phone_number_value(value):
    """Accept common international phone notation; reject malformed API input."""
    normalized = value.strip()
    if len(normalized) > 20:
        raise serializers.ValidationError('Phone number cannot exceed 20 characters.')
    if normalized and not re.fullmatch(r'[0-9+()\\- ]+', normalized):
        raise serializers.ValidationError(
            'Enter a valid phone number using digits, spaces, +, -, and parentheses only.'
        )
    return normalized


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    US-04: User profile update serializer.
    Permits updating name, contact number, and email. Protects role, status, and credentials.
    """

    contact_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    email = serializers.EmailField(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'contact_number', 'email']

    def validate_phone_number(self, value):\n        return validate_phone_number_value(value)\n\n    def validate_contact_number(self, value):\n        return validate_phone_number_value(value)\n\n    def validate_email(self, value):
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError('Email address cannot be empty.')
        user = self.instance
        if User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('A user with that email address already exists.')
        return email

    def validate(self, attrs):
        contact_number = attrs.pop('contact_number', None)
        if contact_number is not None and 'phone_number' not in attrs:
            attrs['phone_number'] = contact_number
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    US-04: Secure password change with current password verification and policy enforcement.
    """

    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )
    new_password_confirm = serializers.CharField(
        required=False,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        current_password = attrs['current_password']
        new_password = attrs['new_password']
        new_password_confirm = attrs.get('new_password_confirm')

        if current_password == new_password:
            raise serializers.ValidationError({
                'new_password': ['New password cannot be the same as the current password.']
            })

        if new_password_confirm is not None and new_password != new_password_confirm:
            raise serializers.ValidationError({
                'new_password_confirm': ['Passwords do not match.']
            })

        try:
            validate_password_policy(new_password, user=user)
        except serializers.ValidationError as e:
            if isinstance(e.detail, dict) and 'password' in e.detail:
                raise serializers.ValidationError({'new_password': e.detail['password']})
            raise
        return attrs

    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        with transaction.atomic():
            user.set_password(new_password)
            user.token_version += 1
            user.save(update_fields=['password', 'token_version'])
        return user


class LoginSerializer(serializers.Serializer):
    """Validates user credentials (username or email) and produces JWT token pair with user context."""

    username = serializers.CharField(
        required=True,
        write_only=True,
        help_text='Accepts either canonical username or registered email address.',
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        raw_identifier = attrs.get('username', '').strip()
        password = attrs.get('password', '')

        if not raw_identifier or not password:
            raise serializers.ValidationError({
                'non_field_errors': ['Must include both username/email and password.']
            })

        # Resolve identifier: allow direct username or registered email address
        lookup_username = raw_identifier
        if '@' in raw_identifier:
            user_by_email = User.objects.filter(email__iexact=raw_identifier).first()
            if user_by_email:
                lookup_username = user_by_email.username

        user = authenticate(username=lookup_username, password=password)

        if not user:
            # Generic message prevents leaking whether the username or email exists
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


class RegisterSerializer(serializers.Serializer):
    """
    Public Customer self-registration serializer.
    Enforces DEC-13 (Customer role only, NFR-SEC-02), unique username/email,
    password complexity (SAD §5.1), and returns user + JWT token pair.
    """

    username = serializers.CharField(
        required=True,
        max_length=150,
        write_only=True,
    )
    email = serializers.EmailField(
        required=True,
        max_length=254,
        write_only=True,
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate_username(self, value):
        username = value.strip()
        if not username:
            raise serializers.ValidationError('Username cannot be empty.')
        if not re.match(r'^[\w.@+-]+$', username):
            raise serializers.ValidationError(
                'Enter a valid username. Letters, digits and @/./+/-/_ only.'
            )
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return username

    def validate_email(self, value):
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError('Email address cannot be empty.')
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('A user with that email address already exists.')
        return email

    def validate(self, attrs):
        password = attrs.get('password', '')
        password_confirm = attrs.get('password_confirm', '')

        if password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': ['Passwords do not match.']
            })

        # Validate password complexity per SAD §5.1
        validate_password_policy(password)

        return attrs

    def create(self, validated_data):
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']

        # Enforce Customer role safeguard (DEC-13 / NFR-SEC-02)
        # Any client-supplied privileges or role fields are ignored/overridden
        with transaction.atomic():
            user = User(
                username=username,
                email=email,
                role='Customer',
                status='active',
                is_active=True,
                is_staff=False,
                is_superuser=False,
                token_version=1,
            )
            user.set_password(password)
            user.save()

        # Issue JWT tokens for instant authenticated session
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
        if type(token_version) is not int or token_version != user.token_version:
            raise exceptions.AuthenticationFailed('Token has been revoked.')

        # Blacklist old refresh token and rotate to a new one atomically
        with transaction.atomic():
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
