from django.contrib.auth import get_user_model
from django.test import TestCase
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AdminUserManagementTests(TestCase):
    """
    US-03: Administrator User Account Management Tests.
    Verifies AC-1, AC-2, AC-3 and RBAC security boundaries.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_boss',
            email='admin@parking.local',
            password='Password123!',
            role='Admin',
            status='active',
        )
        self.operator = User.objects.create_user(
            username='operator_joe',
            email='joe@parking.local',
            password='Password123!',
            role='Operator',
            status='active',
        )
        self.customer = User.objects.create_user(
            username='customer_jane',
            email='jane@parking.local',
            password='Password123!',
            role='Customer',
            status='active',
        )
        self.client = APIClient()

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 3)

    def test_non_admin_cannot_list_or_create_users(self):
        # Operator denied
        self.client.force_authenticate(user=self.operator)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Customer denied
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Unauthenticated denied
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_ac1_admin_creates_operator_account_with_hashed_password(self):
        """AC-1: Admin creates operator/customer account; password stored hashed."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            'username': 'new_operator',
            'email': 'new_operator@parking.local',
            'password': 'SecurePassword123!',
            'role': 'Operator',
        }
        response = self.client.post('/api/auth/users/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'new_operator')
        self.assertEqual(response.data['role'], 'Operator')
        self.assertEqual(response.data['status'], 'active')

        # Verify password is saved and hashed
        created_user = User.objects.get(username='new_operator')
        self.assertNotEqual(created_user.password, 'SecurePassword123!')
        self.assertTrue(created_user.check_password('SecurePassword123!'))

    def test_ac1_admin_creates_customer_account(self):
        """AC-1: Admin creates customer account."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            'username': 'new_customer',
            'email': 'new_customer@parking.local',
            'password': 'CustomerPass123!',
            'role': 'Customer',
        }
        response = self.client.post('/api/auth/users/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'Customer')

    def test_ac3_duplicate_username_returns_409_conflict(self):
        """AC-3: Duplicate username returns HTTP 409 Conflict."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            'username': 'operator_joe',  # Already exists in setUp
            'email': 'unique_email@parking.local',
            'password': 'ValidPassword123!',
            'role': 'Operator',
        }
        response = self.client.post('/api/auth/users/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('username', response.data.get('details', {}))

    def test_ac3_duplicate_email_returns_409_conflict(self):
        """AC-3: Duplicate email returns HTTP 409 Conflict."""
        self.client.force_authenticate(user=self.admin)
        payload = {
            'username': 'unique_joe',
            'email': 'joe@parking.local',  # Already exists in setUp
            'password': 'ValidPassword123!',
            'role': 'Operator',
        }
        response = self.client.post('/api/auth/users/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('email', response.data.get('details', {}))

    def test_ac2_admin_updates_status_enforced_immediately(self):
        """AC-2: Updating status to suspended immediately invalidates existing user tokens."""
        # Issue JWT access token for customer
        refresh = RefreshToken.for_user(self.customer)
        refresh['token_version'] = self.customer.token_version
        refresh['role'] = self.customer.role
        refresh['username'] = self.customer.username
        access_token = str(refresh.access_token)

        # Confirm customer can query /api/auth/me/ with token
        user_client = APIClient()
        user_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        me_resp = user_client.get('/api/auth/me/')
        self.assertEqual(me_resp.status_code, status.HTTP_200_OK)

        # Admin suspends customer account
        self.client.force_authenticate(user=self.admin)
        update_resp = self.client.patch(
            f'/api/auth/users/{self.customer.pk}/',
            {'status': 'suspended'},
            format='json',
        )
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(update_resp.data['status'], 'suspended')

        # Customer's existing token MUST be immediately rejected on subsequent request
        me_after_resp = user_client.get('/api/auth/me/')
        self.assertEqual(me_after_resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_cannot_suspend_or_demote_self(self):
        """Security guard: Admin cannot suspend, deactivate, or demote their own account."""
        self.client.force_authenticate(user=self.admin)

        # Attempt to suspend self
        resp_suspend = self.client.patch(
            f'/api/auth/users/{self.admin.pk}/',
            {'status': 'suspended'},
            format='json',
        )
        self.assertEqual(resp_suspend.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt to demote self to Operator
        resp_demote = self.client.patch(
            f'/api/auth/users/{self.admin.pk}/',
            {'role': 'Operator'},
            format='json',
        )
        self.assertEqual(resp_demote.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_suspend_last_active_admin(self):
        """Security guard: Cannot suspend the last active administrator."""
        self.client.force_authenticate(user=self.admin)
        # self.admin is the only Admin in the system
        resp = self.client.patch(
            f'/api/auth/users/{self.admin.pk}/',
            {'status': 'deactivated'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_cannot_create_another_admin_account(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/auth/users/", {
            "username": "new_admin",
            "email": "new_admin@parking.local",
            "password": "SecurePassword123!",
            "role": "Admin",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="new_admin").exists())

    def test_admin_can_change_role_and_emits_integration_signal(self):
        from accounts.events import user_account_changed
        received = []
        def receiver(sender, event, **kwargs):
            received.append(event)
        user_account_changed.connect(receiver, weak=False)
        try:
            self.client.force_authenticate(user=self.admin)
            response = self.client.patch(
                f"/api/auth/users/{self.customer.pk}/",
                {"role": "Operator"}, format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["role"], "Operator")
            self.assertEqual(len(received), 1)
            self.assertEqual(received[0].event_type, "ROLE_CHANGED")
            self.assertEqual(received[0].previous_state["role"], "Customer")
            self.assertEqual(received[0].new_state["role"], "Operator")
        finally:
            user_account_changed.disconnect(receiver)

    def test_last_active_admin_cannot_be_demoted(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/auth/users/{self.admin.pk}/", {"role": "Operator"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, "Admin")

    def test_case_insensitive_duplicate_username_returns_409(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/auth/users/", {
            "username": "OPERATOR_JOE",
            "email": "another-unique@parking.local",
            "password": "ValidPassword123!",
            "role": "Operator",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("username", response.data.get("details", {}))

    def test_case_insensitive_duplicate_email_returns_409(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/auth/users/", {
            "username": "unique_case_user",
            "email": "JOE@PARKING.LOCAL",
            "password": "ValidPassword123!",
            "role": "Operator",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("email", response.data.get("details", {}))

    def test_database_enforces_case_insensitive_username_uniqueness(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(
                    username="OPERATOR_JOE",
                    email="different@parking.local",
                    password="Password123!",
                    role="Operator",
                )

    def test_receiver_failure_does_not_fail_create_or_lose_account(self):
        from accounts.events import user_account_changed
        def failing_receiver(sender, event, **kwargs):
            raise RuntimeError("simulated downstream outage")
        user_account_changed.connect(failing_receiver, weak=False)
        try:
            self.client.force_authenticate(user=self.admin)
            response = self.client.post("/api/auth/users/", {
                "username": "receiver_failure_user",
                "email": "receiver_failure@parking.local",
                "password": "ValidPassword123!",
                "role": "Operator",
            }, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertTrue(User.objects.filter(username="receiver_failure_user").exists())
        finally:
            user_account_changed.disconnect(failing_receiver)

    def test_receiver_failure_does_not_fail_update_or_lose_change(self):
        from accounts.events import user_account_changed
        def failing_receiver(sender, event, **kwargs):
            raise RuntimeError("simulated downstream outage")
        user_account_changed.connect(failing_receiver, weak=False)
        try:
            self.client.force_authenticate(user=self.admin)
            response = self.client.patch(
                f"/api/auth/users/{self.customer.pk}/",
                {"role": "Operator"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.customer.refresh_from_db()
            self.assertEqual(self.customer.role, "Operator")
        finally:
            user_account_changed.disconnect(failing_receiver)
