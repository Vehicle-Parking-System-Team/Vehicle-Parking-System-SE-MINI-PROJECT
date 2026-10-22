from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.permissions import IsAuthenticatedAndActive
from accounts.serializers import (
    CustomTokenRefreshSerializer,
    LoginSerializer,
    LogoutSerializer,
    UserSerializer,
)


class LoginView(APIView):
    """
    Authenticate user with credentials and return JWT token pair and profile.
    US-01 / FR-15.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Secure logout invalidating refresh token and revoking active access tokens.
    US-01 / FR-15 / FR-17.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token_str = serializer.validated_data['refresh']

        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
        except Exception:
            raise exceptions.AuthenticationFailed('Invalid or already revoked token.')

        # Revoke existing access tokens immediately by incrementing token_version
        user = request.user
        user.token_version += 1
        user.save(update_fields=['token_version'])

        return Response(
            {'message': 'Successfully logged out.'},
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(APIView):
    """
    Issue new access and rotated refresh token using valid refresh token.
    US-01 / FR-15.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomTokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    """
    Retrieve current authenticated user context to verify protected route access.
    US-01 / FR-15, US-02 / FR-16.
    """

    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
