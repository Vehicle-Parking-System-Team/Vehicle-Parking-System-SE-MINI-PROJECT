from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ProfileAndPasswordManagementTests(TestCase):
    """
    US-04: Profile & Password Management Tests.
    Verifies AC-1, AC-2, AC-3, authorization boundaries, and security safeguards.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='user_alice',
            email='alice@parking.local',
            password='OriginalPassword123!',
            role='Customer',
            status='active',
        )
        self.other_user = User.objects.create_user(
            username='user_bob',
            email='bob@parking.local',
            password='OriginalPassword123!',
            role='Customer',
            status='active',
        )
        self.client = APIClient()

    def test_authenticated_user_can_view_own_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user_alice')
        self.assertEqual(response.data['email'], 'alice@parking.local')
        self.assertEqual(response.data['role'], 'Customer')

    def test_ac1_update_profile_name_and_contact(self):
        """AC-1: Authenticated user updates name and contact details successfully."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'first_name': 'Alice',
            'last_name': 'Smith',
            'contact_number': '+91-9876543210',
        }
        response = self.client.patch('/api/auth/profile/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Alice')
        self.assertEqual(response.data['last_name'], 'Smith')
        self.assertEqual(response.data['phone_number'], '+91-9876543210')

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Alice')
        self.assertEqual(self.user.last_name, 'Smith')
        self.assertEqual(self.user.phone_number, '+91-9876543210')

    def test_user_cannot_escalate_role_or_status_via_profile_update(self):
        """Security: Users cannot escalate role or alter status via profile update."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'role': 'Admin',
            'status': 'suspended',
            'first_name': 'Hacker',
        }
        response = self.client.patch('/api/auth/profile/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'Customer')
        self.assertEqual(self.user.status, 'active')
        self.assertEqual(self.user.first_name, 'Hacker')

    def test_duplicate_email_update_rejected(self):
        """Validation: Updating email to another existing user's email is rejected."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'email': 'bob@parking.local',
        }
        response = self.client.patch('/api/auth/profile/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data.get('details', {}))

    def test_ac2_secure_password_change_success(self):
        """AC-2: Valid current password and compliant new password updates and hashes successfully."""
        # Issue JWT access token for user
        refresh = RefreshToken.for_user(self.user)
        refresh['token_version'] = self.user.token_version
        refresh['role'] = self.user.role
        refresh['username'] = self.user.username
        refresh_token = str(refresh)
        access_token = str(refresh.access_token)

        user_client = APIClient()
        user_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        payload = {
            'current_password': 'OriginalPassword123!',
            'new_password': 'NewSecurePassword456!',
            'new_password_confirm': 'NewSecurePassword456!',
        }
        response = user_client.post('/api/auth/password/change/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('message'), 'Password changed successfully.')

        # Verify password is encrypted and persisted
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePassword456!'))
        self.assertFalse(self.user.check_password('OriginalPassword123!'))

        # Token version incremented: old token is revoked on subsequent request
        profile_after = user_client.get('/api/auth/me/')
        self.assertEqual(profile_after.status_code, status.HTTP_401_UNAUTHORIZED)

        # A refresh token issued before the password change must also be rejected.
        refresh_after = self.client.post(
            '/api/auth/token/refresh/', {'refresh': refresh_token}, format='json'
        )
        self.assertEqual(refresh_after.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_rejects_malformed_phone_number(self):
        """The API rejects invalid characters and malformed punctuation for both field names."""
        self.client.force_authenticate(user=self.user)
        invalid_values = (
            '123-ABC-7890',  # unsupported letters
            '++()',          # no digits and repeated plus
            ')(',            # closing parenthesis before opening
            '12+345',        # plus sign outside the beginning
            '(123',          # unclosed parenthesis
            '123)',          # unmatched closing parenthesis
            '---',           # no digits
        )
        for field in ('phone_number', 'contact_number'):
            for value in invalid_values:
                with self.subTest(field=field, value=value):
                    response = self.client.patch(
                        '/api/auth/profile/', {field: value}, format='json'
                    )
                    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                    self.assertIn(field, response.data.get('details', {}))

    def test_profile_accepts_well_formed_phone_number_formats(self):
        """The API continues to accept international and parenthesized phone formats."""
        self.client.force_authenticate(user=self.user)
        for value in ('+91-9876543210', '+1 (555) 123-4567', '98765 43210'):
            with self.subTest(value=value):
                response = self.client.patch(
                    '/api/auth/profile/', {'phone_number': value}, format='json'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['phone_number'], value)

    def test_profile_accepts_blank_optional_phone_number(self):
        """Phone number is optional and can be cleared."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            '/api/auth/profile/', {'phone_number': ''}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], '')

    def test_ac3_incorrect_current_password_returns_400(self):
        """AC-3: Incorrect current password returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'current_password': 'WrongPassword123!',
            'new_password': 'NewSecurePassword456!',
        }
        response = self.client.post('/api/auth/password/change/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_password', response.data.get('details', {}))

    def test_ac3_weak_new_password_violating_policy_returns_400(self):
        """AC-3: Weak new password violating complexity rules returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'current_password': 'OriginalPassword123!',
            'new_password': 'weak',
        }
        response = self.client.post('/api/auth/password/change/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data.get('details', {}))

    def test_ac3_same_new_password_returns_400(self):
        """AC-3: New password identical to current password returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'current_password': 'OriginalPassword123!',
            'new_password': 'OriginalPassword123!',
        }
        response = self.client.post('/api/auth/password/change/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data.get('details', {}))

    def test_password_mismatch_returns_400(self):
        """Validation: Password confirmation mismatch returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.user)
        payload = {
            'current_password': 'OriginalPassword123!',
            'new_password': 'NewSecurePassword456!',
            'new_password_confirm': 'DifferentPassword789!',
        }
        response = self.client.post('/api/auth/password/change/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password_confirm', response.data.get('details', {}))

    def test_unauthenticated_requests_rejected(self):
        """Authorization: Unauthenticated requests are rejected with 401."""
        self.client.force_authenticate(user=None)
        resp_profile = self.client.get('/api/auth/profile/')
        self.assertEqual(resp_profile.status_code, status.HTTP_401_UNAUTHORIZED)

        resp_pwd = self.client.post('/api/auth/password/change/', {})
        self.assertEqual(resp_pwd.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_suspended_account_rejected(self):
        """Authorization: Suspended account is rejected with 403."""
        self.user.status = 'suspended'
        self.user.save()
        self.client.force_authenticate(user=self.user)

        resp_profile = self.client.get('/api/auth/profile/')
        self.assertEqual(resp_profile.status_code, status.HTTP_403_FORBIDDEN)

