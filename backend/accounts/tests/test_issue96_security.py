from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class Issue96SecurityRegressionTests(TestCase):
    def test_createsuperuser_sets_domain_admin_role(self):
        user = User.objects.create_superuser(
            username='issue96_root',
            email='issue96_root@example.test',
            password='SecurePassword123!',
        )
        self.assertEqual(user.role, 'Admin')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_admin_demotion_clears_django_privileges_and_revokes_tokens(self):
        actor = User.objects.create_user(
            username='issue96_actor', password='SecurePassword123!', role='Admin',
        )
        target = User.objects.create_user(
            username='issue96_target', password='SecurePassword123!', role='Admin',
            is_staff=True, is_superuser=True,
        )
        original_version = target.token_version
        client = APIClient()
        client.force_authenticate(user=actor)

        response = client.patch(
            f'/api/auth/users/{target.pk}/',
            {'role': 'Customer'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        target.refresh_from_db()
        self.assertEqual(target.role, 'Customer')
        self.assertFalse(target.is_staff)
        self.assertFalse(target.is_superuser)
        self.assertEqual(target.token_version, original_version + 1)

    def test_logout_blacklists_refresh_without_access_token(self):
        user = User.objects.create_user(
            username='issue96_logout', password='SecurePassword123!', role='Customer',
        )
        refresh = RefreshToken.for_user(user)
        refresh['token_version'] = user.token_version
        client = APIClient()

        response = client.post(
            '/api/auth/logout/',
            {'refresh': str(refresh)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.token_version, 2)

        # Reuse of the same refresh token must fail after logout.
        refresh_response = client.post(
            '/api/auth/token/refresh/',
            {'refresh': str(refresh)},
            format='json',
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_auth_rejects_suspended_and_deactivated_accounts(self):
        for account_status in ('suspended', 'deactivated'):
            with self.subTest(account_status=account_status):
                user = User.objects.create_user(
                    username=f'issue96_{account_status}',
                    password='SecurePassword123!',
                    role='Customer',
                    status=account_status,
                    is_active=True,
                )
                client = APIClient()
                client.force_login(user)
                response = client.get('/api/auth/me/')
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
