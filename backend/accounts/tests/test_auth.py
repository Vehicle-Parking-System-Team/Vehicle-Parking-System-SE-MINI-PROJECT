"""
Automated backend tests for US-01: Authenticate and logout.
Traceability: FR-15, FR-16, FR-17 | UC-01 (TC-UC01-UNIT-001, TC-UC01-API-001)
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()


class AuthenticationTests(TestCase):
    """Integration test suite for login, logout, token refresh, and protected endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.password = 'SecurePass123!'
        self.user = User.objects.create_user(
            username='testoperator',
            email='operator@parking.local',
            password=self.password,
            role='Operator',
            status='active',
        )

    def test_login_success_returns_jwt_pair_and_user_profile(self):
        """Valid credentials return 200, JWT token pair, and user profile."""
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testoperator')
        self.assertEqual(data['user']['role'], 'Operator')
        self.assertEqual(data['user']['status'], 'active')

        # Verify claims embedded in access token
        access_token = AccessToken(data['access'])
        self.assertEqual(access_token['username'], 'testoperator')
        self.assertEqual(access_token['role'], 'Operator')
        self.assertEqual(access_token['token_version'], self.user.token_version)

    def test_login_invalid_password_returns_401_with_generic_message(self):
        """Invalid password returns 401 without leaking credential specifics."""
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': 'WrongPassword999'},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error'], 'Invalid username or password.')

    def test_login_unknown_user_returns_401_with_identical_generic_message(self):
        """Non-existent username returns the exact same 401 message (anti-enumeration)."""
        response = self.client.post(
            '/api/auth/login/',
            {'username': 'nonexistentuser', 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error'], 'Invalid username or password.')

    def test_login_missing_credentials_returns_400(self):
        """Missing username or password returns 400 validation error."""
        response = self.client.post('/api/auth/login/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 'VALIDATION_ERROR')

    def test_login_inactive_user_rejected(self):
        """Users with is_active=False cannot authenticate."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')

    def test_login_suspended_user_rejected(self):
        """Users with status='suspended' cannot authenticate."""
        self.user.status = 'suspended'
        self.user.save()

        response = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')

    def test_login_deactivated_user_rejected(self):
        """Users with status='deactivated' cannot authenticate."""
        self.user.status = 'deactivated'
        self.user.save()

        response = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, 401)

    def test_protected_route_accessible_with_valid_bearer_token(self):
        """Protected endpoint /api/auth/me/ returns 200 with valid Bearer token."""
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['username'], 'testoperator')
        self.assertEqual(data['role'], 'Operator')

    def test_protected_route_rejected_without_token(self):
        """Protected endpoint /api/auth/me/ returns 401 when no token is supplied."""
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_REQUIRED')

    def test_protected_route_rejected_with_invalid_token(self):
        """Protected endpoint returns 401 when invalid token is supplied."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.garbage.token')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 401)

    def test_token_refresh_flow(self):
        """Valid refresh token yields a new access token and rotated refresh token."""
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        refresh_token = login_resp.json()['refresh']

        refresh_resp = self.client.post(
            '/api/auth/token/refresh/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(refresh_resp.status_code, 200)
        data = refresh_resp.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)

        # Confirm new access token works
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
        me_resp = self.client.get('/api/auth/me/')
        self.assertEqual(me_resp.status_code, 200)

    def test_logout_blacklists_refresh_token(self):
        """Logout blacklists the refresh token preventing subsequent refresh attempts."""
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']
        refresh_token = login_resp.json()['refresh']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout_resp = self.client.post(
            '/api/auth/logout/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(logout_resp.status_code, 200)
        self.assertEqual(logout_resp.json()['message'], 'Successfully logged out.')

        # Attempt to use the blacklisted refresh token
        reuse_resp = self.client.post(
            '/api/auth/token/refresh/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(reuse_resp.status_code, 401)

    def test_logout_immediately_revokes_already_issued_access_token(self):
        """
        US-01 requirement: Logout must genuinely revoke access.
        The already-issued access token is immediately rejected on protected routes.
        """
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']
        refresh_token = login_resp.json()['refresh']

        # Confirm access token is currently valid
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        pre_logout_resp = self.client.get('/api/auth/me/')
        self.assertEqual(pre_logout_resp.status_code, 200)

        # Perform logout
        logout_resp = self.client.post(
            '/api/auth/logout/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(logout_resp.status_code, 200)

        # Attempt to access protected route with the pre-logout access token
        post_logout_resp = self.client.get('/api/auth/me/')
        self.assertEqual(post_logout_resp.status_code, 401)
        data = post_logout_resp.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertIn('revoked', data['error'].lower())

    def test_logout_missing_refresh_token_returns_400(self):
        """Logout request without refresh token returns 400."""
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post('/api/auth/logout/', {}, format='json')
        self.assertEqual(response.status_code, 400)
