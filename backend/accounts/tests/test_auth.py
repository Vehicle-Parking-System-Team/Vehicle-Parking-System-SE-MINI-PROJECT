"""
Automated backend tests for US-01: Authenticate and logout.
Traceability: FR-15, FR-16, FR-17 | UC-01 (TC-UC01-UNIT-001, TC-UC01-API-001)
"""

from unittest.mock import patch

import django.db
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
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
        self.assertEqual(data['error'], 'Authentication failed.')

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
        self.assertEqual(data['error'], 'Authentication failed.')

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
        self.assertEqual(data['error'], 'Authentication failed.')

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

    def test_logout_cross_user_token_rejected_without_state_change(self):
        """
        Cross-user logout security: User A cannot blacklist User B's refresh token.
        User B's token remains valid, B's state is untouched, and A's session is unaffected.
        """
        user_b = User.objects.create_user(
            username='user_b',
            email='user_b@parking.local',
            password='PasswordB123!',
            role='Customer',
            status='active',
        )

        login_a = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_a = login_a.json()['access']
        refresh_a = login_a.json()['refresh']

        login_b = self.client.post(
            '/api/auth/login/',
            {'username': 'user_b', 'password': 'PasswordB123!'},
            format='json',
        )
        refresh_b = login_b.json()['refresh']
        access_b = login_b.json()['access']

        initial_b_version = user_b.token_version
        initial_a_version = self.user.token_version

        # User A attempts to log out with User B's refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_a}')
        cross_logout_resp = self.client.post(
            '/api/auth/logout/',
            {'refresh': refresh_b},
            format='json',
        )
        self.assertEqual(cross_logout_resp.status_code, 401)
        data = cross_logout_resp.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error'], 'Authentication failed.')

        # Verify User B's state was NOT modified
        user_b.refresh_from_db()
        self.assertEqual(user_b.token_version, initial_b_version)
        self.assertEqual(user_b.status, 'active')

        # Verify User B's refresh token was NOT blacklisted (can still be refreshed)
        self.client.credentials()  # clear credentials
        refresh_resp = self.client.post(
            '/api/auth/token/refresh/',
            {'refresh': refresh_b},
            format='json',
        )
        self.assertEqual(refresh_resp.status_code, 200)

        # Verify User B's access token is still valid
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_b}')
        me_resp_b = self.client.get('/api/auth/me/')
        self.assertEqual(me_resp_b.status_code, 200)

        # Verify User A's session and state were NOT revoked or changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_version, initial_a_version)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_a}')
        me_resp_a = self.client.get('/api/auth/me/')
        self.assertEqual(me_resp_a.status_code, 200)

    def test_logout_with_malformed_token_returns_401(self):
        """Malformed refresh token in logout returns 401 and leaves state unchanged."""
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']
        initial_version = self.user.token_version

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(
            '/api/auth/logout/',
            {'refresh': 'malformed.garbage.token'},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error'], 'Authentication failed.')

        # State unchanged, access token still valid
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_version, initial_version)
        me_resp = self.client.get('/api/auth/me/')
        self.assertEqual(me_resp.status_code, 200)

    def test_logout_with_already_blacklisted_token_returns_401(self):
        """Supplying an already blacklisted refresh token returns 401."""
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']
        refresh_token = login_resp.json()['refresh']

        # First legitimate logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        logout1 = self.client.post(
            '/api/auth/logout/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(logout1.status_code, 200)

        # Clear credentials and login again to get new session
        self.client.credentials()
        login_resp2 = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        self.assertEqual(login_resp2.status_code, 200)
        access_token2 = login_resp2.json()['access']
        self.user.refresh_from_db()
        version_before = self.user.token_version

        # Attempt to reuse old blacklisted refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token2}')
        logout2 = self.client.post(
            '/api/auth/logout/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(logout2.status_code, 401)
        data = logout2.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error'], 'Authentication failed.')

        # State untouched, second session still active
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_version, version_before)
        me_resp = self.client.get('/api/auth/me/')
        self.assertEqual(me_resp.status_code, 200)

    def test_logout_with_superseded_token_version_rejected(self):
        """A refresh token from an older token_version is rejected even if not yet blacklisted."""
        # Create token with old token_version
        old_refresh = RefreshToken.for_user(self.user)
        old_refresh['token_version'] = self.user.token_version

        # Increment token_version on user
        self.user.token_version += 1
        self.user.save(update_fields=['token_version'])

        # Issue new valid access token for current version
        new_refresh = RefreshToken.for_user(self.user)
        new_refresh['token_version'] = self.user.token_version
        current_access = str(new_refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {current_access}')
        response = self.client.post(
            '/api/auth/logout/',
            {'refresh': str(old_refresh)},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error'], 'Authentication failed.')

    def test_logout_unexpected_server_failure_returns_sanitized_500(self):
        """
        Unexpected server exceptions during blacklist/revocation are NOT converted
        into 401 auth errors. They propagate to produce a sanitized 500 INTERNAL_ERROR
        without leaking secrets or tokens into responses or logs.
        """
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']
        refresh_token = login_resp.json()['refresh']
        secret_leak = 'RAW_DB_PASSWORD_LEAK_SECRET_98765'

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        initial_version = self.user.token_version

        with patch.object(RefreshToken, 'blacklist', side_effect=RuntimeError(secret_leak)):
            with self.assertLogs('common.exceptions', level='ERROR') as captured_logs:
                response = self.client.post(
                    '/api/auth/logout/',
                    {'refresh': refresh_token},
                    format='json',
                )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 'INTERNAL_ERROR')
        self.assertEqual(data['error'], 'An unexpected error occurred.')
        self.assertEqual(data['details'], {})

        # Assert secret value does NOT appear in response body
        self.assertNotIn(secret_leak, response.content.decode())

        # Assert diagnostic log does NOT contain the secret string (safe traceback policy)
        full_log = '\n'.join(captured_logs.output)
        self.assertNotIn(secret_leak, full_log)
        self.assertIn('LogoutView', full_log)

        # Assert user token_version was NOT incremented on failed logout
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_version, initial_version)

    def test_token_refresh_unexpected_server_failure_returns_sanitized_500(self):
        """
        Unexpected server exceptions during token refresh are NOT converted into
        401 auth errors.
        """
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        refresh_token = login_resp.json()['refresh']
        secret_leak = 'REFRESH_DB_DISASTER_SECRET_54321'

        with patch.object(RefreshToken, 'blacklist', side_effect=RuntimeError(secret_leak)):
            with self.assertLogs('common.exceptions', level='ERROR') as captured_logs:
                response = self.client.post(
                    '/api/auth/token/refresh/',
                    {'refresh': refresh_token},
                    format='json',
                )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 'INTERNAL_ERROR')
        self.assertEqual(data['error'], 'An unexpected error occurred.')
        self.assertNotIn(secret_leak, response.content.decode())
        self.assertNotIn(secret_leak, '\n'.join(captured_logs.output))

    def test_logout_with_missing_token_version_rejected(self):
        """Logout rejects refresh tokens missing the required token_version claim."""
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']
        initial_version = self.user.token_version

        # Craft a refresh token missing token_version
        token = RefreshToken.for_user(self.user)
        token.payload.pop('token_version', None)
        jti = token.payload['jti']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(
            '/api/auth/logout/',
            {'refresh': str(token)},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error'], 'Authentication failed.')

        # Ensure state unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_version, initial_version)
        self.assertFalse(BlacklistedToken.objects.filter(token__jti=jti).exists())

    def test_refresh_with_missing_token_version_rejected(self):
        """Token refresh rejects refresh tokens missing the required token_version claim."""
        token = RefreshToken.for_user(self.user)
        token.payload.pop('token_version', None)

        response = self.client.post(
            '/api/auth/token/refresh/',
            {'refresh': str(token)},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
        self.assertEqual(data['error'], 'Authentication failed.')

    def test_logout_with_malformed_token_version_claims_rejected(self):
        """Logout rejects tokens with null, string, boolean, or mismatched token_version claims."""
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'testoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']
        initial_version = self.user.token_version
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        malformed_values = [None, 'invalid_str', True, 999]
        for val in malformed_values:
            with self.subTest(token_version=val):
                token = RefreshToken.for_user(self.user)
                token['token_version'] = val

                response = self.client.post(
                    '/api/auth/logout/',
                    {'refresh': str(token)},
                    format='json',
                )
                self.assertEqual(response.status_code, 401)
                data = response.json()
                self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
                self.assertEqual(data['error'], 'Authentication failed.')

                self.user.refresh_from_db()
                self.assertEqual(self.user.token_version, initial_version)

    def test_refresh_with_malformed_token_version_claims_rejected(self):
        """Token refresh rejects tokens with null, string, boolean, or mismatched token_version claims."""
        malformed_values = [None, 'invalid_str', True, 999]
        for val in malformed_values:
            with self.subTest(token_version=val):
                token = RefreshToken.for_user(self.user)
                token['token_version'] = val

                response = self.client.post(
                    '/api/auth/token/refresh/',
                    {'refresh': str(token)},
                    format='json',
                )
                self.assertEqual(response.status_code, 401)
                data = response.json()
                self.assertEqual(data['code'], 'AUTHENTICATION_FAILED')
                self.assertEqual(data['error'], 'Authentication failed.')

    def test_protected_route_with_missing_or_malformed_token_version_rejected(self):
        """Access token authentication rejects tokens missing or carrying malformed token_version."""
        # 1. Missing token_version
        token = RefreshToken.for_user(self.user)
        access = token.access_token
        access.payload.pop('token_version', None)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['code'], 'AUTHENTICATION_FAILED')

        # 2. String token_version
        token = RefreshToken.for_user(self.user)
        access = token.access_token
        access['token_version'] = 'bad_version'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['code'], 'AUTHENTICATION_FAILED')

        # 3. Boolean token_version
        token = RefreshToken.for_user(self.user)
        access = token.access_token
        access['token_version'] = True
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['code'], 'AUTHENTICATION_FAILED')

        # 4. Mismatched token_version
        token = RefreshToken.for_user(self.user)
        access = token.access_token
        access['token_version'] = 999
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['code'], 'AUTHENTICATION_FAILED')


class LogoutAtomicityTests(TransactionTestCase):
    """
    TransactionTestCase suite to verify genuine database rollback behavior
    for atomic logout and error scenarios.
    """

    def setUp(self):
        self.client = APIClient()
        self.password = 'SecurePass123!'
        self.user = User.objects.create_user(
            username='atomicoperator',
            email='atomic@parking.local',
            password=self.password,
            role='Operator',
            status='active',
        )

    def test_logout_atomic_rollback_when_user_save_fails(self):
        """
        Verify atomicity: If user.save fails after token.blacklist() in LogoutView,
        the transaction rolls back completely. Neither the blacklist record nor
        the token_version update persists in the actual database.
        """
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'atomicoperator', 'password': self.password},
            format='json',
        )
        self.assertEqual(login_resp.status_code, 200)
        access_token = login_resp.json()['access']
        refresh_token = login_resp.json()['refresh']

        jti = RefreshToken(refresh_token).payload['jti']
        initial_version = self.user.token_version

        # Verify not yet blacklisted
        self.assertFalse(BlacklistedToken.objects.filter(token__jti=jti).exists())

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        with patch.object(User, 'save', side_effect=django.db.DatabaseError('SIMULATED_DB_WRITE_FAILURE')):
            response = self.client.post(
                '/api/auth/logout/',
                {'refresh': refresh_token},
                format='json',
            )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 'INTERNAL_ERROR')

        # CRITICAL ATOMICITY ASSERTIONS:
        # 1. token_version in the database was NOT incremented
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_version, initial_version)

        # 2. BlacklistedToken record was rolled back from the database
        self.assertFalse(BlacklistedToken.objects.filter(token__jti=jti).exists())

        # 3. Refresh token can still be used because blacklist was rolled back
        self.client.credentials()
        refresh_resp = self.client.post(
            '/api/auth/token/refresh/',
            {'refresh': refresh_token},
            format='json',
        )
        self.assertEqual(refresh_resp.status_code, 200)
        self.assertIn('access', refresh_resp.json())

    def test_logout_atomic_rollback_when_blacklisting_fails(self):
        """
        Verify atomicity: If blacklisting fails, user.save is never reached,
        and user state is unaffected.
        """
        login_resp = self.client.post(
            '/api/auth/login/',
            {'username': 'atomicoperator', 'password': self.password},
            format='json',
        )
        access_token = login_resp.json()['access']
        refresh_token = login_resp.json()['refresh']

        initial_version = self.user.token_version
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        with patch.object(RefreshToken, 'blacklist', side_effect=django.db.DatabaseError('SIMULATED_BLACKLIST_FAILURE')):
            response = self.client.post(
                '/api/auth/logout/',
                {'refresh': refresh_token},
                format='json',
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['code'], 'INTERNAL_ERROR')

        self.user.refresh_from_db()
        self.assertEqual(self.user.token_version, initial_version)
