from django.db import models, transaction
from django.utils import timezone
from rest_framework import exceptions, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.permissions import IsAdmin, IsAuthenticatedAndActive
from accounts.events import UserAccountChangeEvent, dispatch_user_account_change
from accounts.serializers import (
    AdminUserCreateSerializer,
    AdminUserListSerializer,
    AdminUserUpdateSerializer,
    CustomTokenRefreshSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    """
    Public self-service Customer registration endpoint.
    DEC-13 / SAD §3.4.2 & §5.1.
    Creates a Customer account, enforces password policy, and returns JWT session pair.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_data = serializer.save()
        return Response(session_data, status=status.HTTP_201_CREATED)


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
        except TokenError:
            raise exceptions.AuthenticationFailed('Invalid or already revoked token.')

        # Verify token ownership: the token must belong to request.user
        token_user_id = token.get(api_settings.USER_ID_CLAIM)
        if str(token_user_id) != str(request.user.pk):
            raise exceptions.AuthenticationFailed('Invalid or already revoked token.')

        # Verify token version: token must have a valid int token_version matching user.token_version
        token_version = token.get('token_version')
        if type(token_version) is not int or token_version != request.user.token_version:
            raise exceptions.AuthenticationFailed('Invalid or already revoked token.')

        with transaction.atomic():
            try:
                token.blacklist()
            except TokenError:
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

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticatedAndActive]
    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
    def put(self, request):
        return self.patch(request)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticatedAndActive]
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)


class AdminUserManagementView(APIView):
    """
    US-03: Administrator user account list and creation endpoint.
    Restricted to authenticated Administrators.
    """

    permission_classes = [IsAdmin]

    def get(self, request):
        users = User.objects.all().order_by('-date_joined', '-pk')
        role_filter = request.query_params.get('role')
        if role_filter:
            users = users.filter(role=role_filter)
        status_filter = request.query_params.get('status')
        if status_filter:
            users = users.filter(status=status_filter)
        search_query = request.query_params.get('search')
        if search_query:
            users = users.filter(
                models.Q(username__icontains=search_query) |
                models.Q(email__icontains=search_query)
            )
        serializer = AdminUserListSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        dispatch_user_account_change(
            UserAccountChangeEvent(
                actor_id=request.user.pk,
                actor_username=request.user.username,
                target_user_id=user.pk,
                target_username=user.username,
                event_type='USER_CREATED',
                previous_state={},
                new_state={'role': user.role, 'status': user.status, 'email': user.email},
                timestamp=timezone.now().isoformat(),
            )
        )
        return Response(AdminUserListSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    """
    US-03: Administrator user account detail and status/role update endpoint.
    Restricted to authenticated Administrators.
    """

    permission_classes = [IsAdmin]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise exceptions.NotFound('The requested user was not found.')

    def get(self, request, pk):
        user = self.get_object(pk)
        return Response(AdminUserListSerializer(user).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        # Serialize admin lifecycle changes under row locks where supported.
        with transaction.atomic():
            # Lock active administrators in a stable order before locking the target.
            # Concurrent admin lifecycle changes therefore serialize without lock-order inversion.
            active_admin_ids = list(
                User.objects.select_for_update()
                .filter(role='Admin', status='active', is_active=True)
                .order_by('pk')
                .values_list('pk', flat=True)
            )
            try:
                user = User.objects.select_for_update().get(pk=pk)
            except User.DoesNotExist:
                raise exceptions.NotFound('The requested user was not found.')
            serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            new_status = serializer.validated_data.get('status')
            new_role = serializer.validated_data.get('role')
            if not new_status and not new_role:
                return Response(AdminUserListSerializer(user).data, status=status.HTTP_200_OK)
            if user.pk == request.user.pk:
                if new_status and new_status != 'active':
                    raise exceptions.ValidationError({'status': 'Administrators cannot suspend or deactivate their own account.'})
                if new_role and new_role != 'Admin':
                    raise exceptions.ValidationError({'role': 'Administrators cannot demote their own account role.'})
            threatens_admin_access = user.role == 'Admin' and ((new_status and new_status != 'active') or (new_role and new_role != 'Admin'))
            if threatens_admin_access:
                if not any(admin_id != user.pk for admin_id in active_admin_ids):
                    raise exceptions.ValidationError({'error': 'Cannot suspend, deactivate, or demote the last active Administrator.'})
            previous_state = {'status': user.status, 'role': user.role}
            status_changed = bool(new_status and new_status != user.status)
            role_changed = bool(new_role and new_role != user.role)
            if status_changed:
                user.status = new_status
                if new_status in ('suspended', 'deactivated'):
                    user.token_version += 1
                user.is_active = new_status == 'active'
            if role_changed:
                user.role = new_role
            if status_changed or role_changed:
                user.save()
        if status_changed or role_changed:
            event_type = 'STATUS_CHANGED' if status_changed and not role_changed else ('ROLE_CHANGED' if role_changed and not status_changed else 'ACCOUNT_UPDATED')
            dispatch_user_account_change(UserAccountChangeEvent(actor_id=request.user.pk, actor_username=request.user.username, target_user_id=user.pk, target_username=user.username, event_type=event_type, previous_state=previous_state, new_state={'status': user.status, 'role': user.role}, timestamp=timezone.now().isoformat()))
        return Response(AdminUserListSerializer(user).data, status=status.HTTP_200_OK)
