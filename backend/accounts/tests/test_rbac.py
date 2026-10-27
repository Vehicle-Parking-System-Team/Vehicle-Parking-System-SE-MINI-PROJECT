"""
Comprehensive automated tests for US-02: Role-Based Access Control (RBAC).
Traceability: US-02 (#22), FR-16, NFR-SEC-01, NFR-SEC-02.
SRS Section 9.2 (Role Hierarchy & RBAC Matrix), SAD Section 3.4.2 & Section 3.9.
"""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import TestCase, override_settings
from django.urls import include, path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from accounts.permissions import (
    BaseRolePermission,
    IsAdmin,
    IsAdminOrOperator,
    IsAuthenticatedAndActive,
    IsCustomer,
    IsOperator,
    IsOwnerOrAdmin,
    IsOwnerOrAdminOrOperator,
    has_roles,
)

User = get_user_model()


class AdminOnlyTestView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({'message': 'Admin access granted.', 'role': request.user.role})


class OperatorOnlyTestView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response({'message': 'Operator access granted.', 'role': request.user.role})


class CustomerOnlyTestView(APIView):
    permission_classes = [IsCustomer]

    def get(self, request):
        return Response({'message': 'Customer access granted.', 'role': request.user.role})


class OperatorOrAdminTestView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        return Response({'message': 'Operations access granted.', 'role': request.user.role})


class UserResourceTestView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request, user_id):
        target_user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(request, target_user)
        return Response({'id': target_user.id, 'username': target_user.username})


urlpatterns = [
    path('api/auth/', include('accounts.urls')),
    path('test/rbac/admin-only/', AdminOnlyTestView.as_view()),
    path('test/rbac/operator-only/', OperatorOnlyTestView.as_view()),
    path('test/rbac/customer-only/', CustomerOnlyTestView.as_view()),
    path('test/rbac/operator-or-admin/', OperatorOrAdminTestView.as_view()),
    path('test/rbac/user-resource/<int:user_id>/', UserResourceTestView.as_view()),
]


@override_settings(ROOT_URLCONF=__name__)
class RBACTests(TestCase):
    """
    Validates server-side authorization enforcement across all documented roles:
    Administrator, Operator, and Customer.
    """

    def setUp(self):
        self.client = APIClient()
        self.password = 'SecurePass123!'

        # Permitted canonical users
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@parking.local',
            password=self.password,
            role='Admin',
            status='active',
        )
        self.operator_user = User.objects.create_user(
            username='operator_user',
            email='operator@parking.local',
            password=self.password,
            role='Operator',
            status='active',
        )
        self.customer1 = User.objects.create_user(
            username='customer_one',
            email='c1@parking.local',
            password=self.password,
            role='Customer',
            status='active',
        )
        self.customer2 = User.objects.create_user(
            username='customer_two',
            email='c2@parking.local',
            password=self.password,
            role='Customer',
            status='active',
        )

        # Ineligible/inactive users
        self.suspended_user = User.objects.create_user(
            username='suspended_user',
            email='suspended@parking.local',
            password=self.password,
            role='Customer',
            status='suspended',
        )
        self.deactivated_user = User.objects.create_user(
            username='deactivated_user',
            email='deactivated@parking.local',
            password=self.password,
            role='Customer',
            status='deactivated',
            is_active=False,
        )

    def _auth_token(self, user):
        """Generate a valid signed access token for the given user."""
        token = AccessToken.for_user(user)
        token['username'] = user.username
        token['role'] = user.role
        token['token_version'] = user.token_version
        return str(token)

    # -------------------------------------------------------------------------
    # 1. Unauthenticated access tests (NFR-SEC-01 -> 401 Unauthorized)
    # -------------------------------------------------------------------------
    def test_unauthenticated_requests_to_protected_endpoints_return_401(self):
        """Unauthenticated requests to any protected endpoint return HTTP 401."""
        endpoints = [
            '/api/auth/me/',
            '/test/rbac/admin-only/',
            '/test/rbac/operator-only/',
            '/test/rbac/customer-only/',
            '/test/rbac/operator-or-admin/',
            f'/test/rbac/user-resource/{self.customer1.id}/',
        ]
        for url in endpoints:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                    f'Expected 401 for unauthenticated request to {url}',
                )
                data = response.json()
                self.assertEqual(data.get('code'), 'AUTHENTICATION_REQUIRED')

    # -------------------------------------------------------------------------
    # 2. Correct access for each permitted role (200 OK)
    # -------------------------------------------------------------------------
    def test_admin_has_access_to_admin_and_operations_endpoints(self):
        """Admin role can access Admin-only, operations, and self profile."""
        token = self._auth_token(self.admin_user)
        auth_header = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

        res_admin = self.client.get('/test/rbac/admin-only/', **auth_header)
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(res_admin.json()['role'], 'Admin')

        res_ops = self.client.get('/test/rbac/operator-or-admin/', **auth_header)
        self.assertEqual(res_ops.status_code, status.HTTP_200_OK)

        res_me = self.client.get('/api/auth/me/', **auth_header)
        self.assertEqual(res_me.status_code, status.HTTP_200_OK)

    def test_operator_has_access_to_operator_and_operations_endpoints(self):
        """Operator role can access Operator-only, operations, and self profile."""
        token = self._auth_token(self.operator_user)
        auth_header = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

        res_op = self.client.get('/test/rbac/operator-only/', **auth_header)
        self.assertEqual(res_op.status_code, status.HTTP_200_OK)
        self.assertEqual(res_op.json()['role'], 'Operator')

        res_ops = self.client.get('/test/rbac/operator-or-admin/', **auth_header)
        self.assertEqual(res_ops.status_code, status.HTTP_200_OK)

        res_me = self.client.get('/api/auth/me/', **auth_header)
        self.assertEqual(res_me.status_code, status.HTTP_200_OK)

    def test_customer_has_access_to_customer_and_self_endpoints(self):
        """Customer role can access Customer-only and self profile."""
        token = self._auth_token(self.customer1)
        auth_header = {'HTTP_AUTHORIZATION': f'Bearer {token}'}

        res_cust = self.client.get('/test/rbac/customer-only/', **auth_header)
        self.assertEqual(res_cust.status_code, status.HTTP_200_OK)
        self.assertEqual(res_cust.json()['role'], 'Customer')

        res_me = self.client.get('/api/auth/me/', **auth_header)
        self.assertEqual(res_me.status_code, status.HTTP_200_OK)

    # -------------------------------------------------------------------------
    # 3. Denial for each role lacking permission (NFR-SEC-01, NFR-SEC-02 -> 403 Forbidden)
    # -------------------------------------------------------------------------
    def test_operator_and_customer_denied_from_admin_endpoints(self):
        """Non-admin roles are forbidden from Admin-only endpoints (NFR-SEC-02)."""
        non_admin_users = [self.operator_user, self.customer1]

        for user in non_admin_users:
            with self.subTest(user=user.username, role=user.role):
                token = self._auth_token(user)
                response = self.client.get(
                    '/test/rbac/admin-only/',
                    HTTP_AUTHORIZATION=f'Bearer {token}',
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                    f'Role {user.role} should be forbidden from admin-only endpoint',
                )
                data = response.json()
                self.assertEqual(data.get('code'), 'PERMISSION_DENIED')

    def test_customer_denied_from_operations_endpoints(self):
        """Customer role is forbidden from operational endpoints (bay mgmt, check-in/out)."""
        token = self._auth_token(self.customer1)
        response = self.client.get(
            '/test/rbac/operator-or-admin/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json().get('code'), 'PERMISSION_DENIED')

    def test_admin_and_customer_denied_from_operator_strict_endpoints(self):
        """Roles other than Operator are denied from Operator-only endpoints."""
        for user in [self.admin_user, self.customer1]:
            with self.subTest(role=user.role):
                token = self._auth_token(user)
                response = self.client.get(
                    '/test/rbac/operator-only/',
                    HTTP_AUTHORIZATION=f'Bearer {token}',
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # 4. Unknown, missing, malformed, or invalid role values (Default Deny)
    # -------------------------------------------------------------------------
    def test_unknown_or_invalid_role_values_denied_by_default(self):
        """Users with null, empty, unknown, or malformed roles are rejected with 403."""
        invalid_roles = ['SuperAdmin', 'Root', 'Manager', '', 'attacker', '1234']

        for invalid_role in invalid_roles:
            with self.subTest(invalid_role=invalid_role):
                user = User.objects.create_user(
                    username=f'user_{abs(hash(invalid_role))}',
                    email=f'test_{abs(hash(invalid_role))}@parking.local',
                    password=self.password,
                    role=invalid_role,
                    status='active',
                )
                self.client.force_authenticate(user=user)
                response = self.client.get('/api/auth/me/')
                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                    f'Role {invalid_role} must default to denying access',
                )
                self.assertEqual(response.json().get('code'), 'PERMISSION_DENIED')

    # -------------------------------------------------------------------------
    # 5. Privilege escalation attempts via payload, query params, headers
    # -------------------------------------------------------------------------
    def test_privilege_escalation_via_request_parameters_is_prevented(self):
        """Client cannot elevate privileges by supplying a fake role in headers, body, or params."""
        token = self._auth_token(self.customer1)

        # Attempt 1: Query parameter tampering (?role=Admin)
        res_param = self.client.get(
            '/test/rbac/admin-only/?role=Admin&is_superuser=true',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(res_param.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt 2: Header tampering (X-Role: Admin)
        res_header = self.client.get(
            '/test/rbac/admin-only/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
            HTTP_X_ROLE='Admin',
            HTTP_X_FORWARDED_ROLE='Admin',
        )
        self.assertEqual(res_header.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt 3: Payload tampering in POST/PUT request
        res_payload = self.client.post(
            '/test/rbac/admin-only/',
            {'role': 'Admin', 'admin': True},
            format='json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertIn(res_payload.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED])

    # -------------------------------------------------------------------------
    # 6. Object-level authorization tests
    # -------------------------------------------------------------------------
    def test_customer_cannot_access_another_customers_resource(self):
        """Customer cannot read or modify another customer's object (403 Forbidden)."""
        token = self._auth_token(self.customer1)
        response = self.client.get(
            f'/test/rbac/user-resource/{self.customer2.id}/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json().get('code'), 'PERMISSION_DENIED')

    def test_customer_can_access_own_resource(self):
        """Customer can access their own object (200 OK)."""
        token = self._auth_token(self.customer1)
        response = self.client.get(
            f'/test/rbac/user-resource/{self.customer1.id}/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], self.customer1.id)
        self.assertEqual(data['username'], self.customer1.username)

    def test_admin_can_access_any_users_resource(self):
        """Administrator has system-wide access to any user resource."""
        token = self._auth_token(self.admin_user)
        for target in [self.customer1, self.customer2, self.operator_user]:
            with self.subTest(target_username=target.username):
                response = self.client.get(
                    f'/test/rbac/user-resource/{target.id}/',
                    HTTP_AUTHORIZATION=f'Bearer {token}',
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json()['id'], target.id)

    # -------------------------------------------------------------------------
    # 7. Safe behavior for inactive, suspended, or deactivated users
    # -------------------------------------------------------------------------
    def test_suspended_user_is_denied_access(self):
        """Suspended user cannot access protected endpoints."""
        self.client.force_authenticate(user=self.suspended_user)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json().get('code'), 'PERMISSION_DENIED')

    def test_deactivated_user_is_denied_access(self):
        """Deactivated user cannot access protected endpoints."""
        self.client.force_authenticate(user=self.deactivated_user)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json().get('code'), 'PERMISSION_DENIED')

    # -------------------------------------------------------------------------
    # 8. Reusable permission classes unit checks
    # -------------------------------------------------------------------------
    # 8. Reusable permission classes unit checks & regression tests
    # -------------------------------------------------------------------------
    def test_has_roles_factory_creates_correct_permission_class(self):
        """has_roles correctly dynamically validates custom combinations of roles."""
        AdminOrCustomer = has_roles('Admin', 'Customer')
        perm = AdminOrCustomer()

        class MockRequest:
            def __init__(self, user):
                self.user = user

        # Allowed roles
        self.assertTrue(perm.has_permission(MockRequest(self.admin_user), None))
        self.assertTrue(perm.has_permission(MockRequest(self.customer1), None))

        # Denied roles
        self.assertFalse(perm.has_permission(MockRequest(self.operator_user), None))

    def test_has_roles_rejects_empty_configuration(self):
        """Regression (Finding 1): has_roles() must reject empty role configurations with ValueError."""
        with self.assertRaises(ValueError) as ctx:
            has_roles()
        self.assertIn('at least one role', str(ctx.exception).lower())

    def test_has_roles_rejects_invalid_or_unsupported_roles(self):
        """Regression (Finding 1): has_roles() must reject configurations containing invalid role names."""
        # All invalid
        with self.assertRaises(ValueError) as ctx1:
            has_roles('Superuser', 'Guest')
        self.assertIn('invalid role', str(ctx1.exception).lower())

        # Mixed valid and invalid
        with self.assertRaises(ValueError) as ctx2:
            has_roles('Admin', 'Manager')
        self.assertIn('invalid role', str(ctx2.exception).lower())

    def test_base_role_permission_fails_closed_on_empty_or_invalid_allowed_roles(self):
        """Regression (Finding 1): BaseRolePermission must fail closed (deny access) if allowed_roles is empty or invalid."""
        class MockRequest:
            def __init__(self, user):
                self.user = user

        req_admin = MockRequest(self.admin_user)

        # Empty allowed_roles
        class EmptyRolesPermission(BaseRolePermission):
            allowed_roles = ()

        self.assertFalse(EmptyRolesPermission().has_permission(req_admin, None))

        # None allowed_roles
        class NoneRolesPermission(BaseRolePermission):
            allowed_roles = None

        self.assertFalse(NoneRolesPermission().has_permission(req_admin, None))

        # Invalid/unrecognized role in allowed_roles
        class InvalidRolesPermission(BaseRolePermission):
            allowed_roles = ('NonExistentRole',)

        self.assertFalse(InvalidRolesPermission().has_permission(req_admin, None))

    def test_object_level_owner_permission_helpers(self):
        """IsOwnerOrAdmin and IsOwnerOrAdminOrOperator helper behavior."""
        class MockResource:
            def __init__(self, owner):
                self.user = owner

        res1 = MockResource(self.customer1)

        perm_owner_admin = IsOwnerOrAdmin()
        perm_owner_ops = IsOwnerOrAdminOrOperator()

        class MockRequest:
            def __init__(self, user):
                self.user = user

        # Owner accesses own resource
        req_c1 = MockRequest(self.customer1)
        self.assertTrue(perm_owner_admin.has_object_permission(req_c1, None, res1))
        self.assertTrue(perm_owner_ops.has_object_permission(req_c1, None, res1))

        # Non-owner accesses resource
        req_c2 = MockRequest(self.customer2)
        self.assertFalse(perm_owner_admin.has_object_permission(req_c2, None, res1))
        self.assertFalse(perm_owner_ops.has_object_permission(req_c2, None, res1))

        # Operator accesses resource
        req_op = MockRequest(self.operator_user)
        self.assertFalse(perm_owner_admin.has_object_permission(req_op, None, res1))
        self.assertTrue(perm_owner_ops.has_object_permission(req_op, None, res1))

        # Admin accesses resource
        req_admin = MockRequest(self.admin_user)
        self.assertTrue(perm_owner_admin.has_object_permission(req_admin, None, res1))
        self.assertTrue(perm_owner_ops.has_object_permission(req_admin, None, res1))

    def test_unrelated_resource_matching_user_id_denies_ownership(self):
        """Regression (Finding 2): Unrelated resources sharing the same ID as a user must be denied ownership."""
        class UnrelatedResource:
            def __init__(self, resource_id):
                self.id = resource_id  # Has an id attribute matching customer1, but NO owner/user field

        unrelated = UnrelatedResource(self.customer1.id)

        perm_owner_admin = IsOwnerOrAdmin()
        perm_owner_ops = IsOwnerOrAdminOrOperator()

        class MockRequest:
            def __init__(self, user):
                self.user = user

        # Customer must be DENIED access to unrelated resource even though id matches user.id
        req_c1 = MockRequest(self.customer1)
        self.assertFalse(perm_owner_admin.has_object_permission(req_c1, None, unrelated))
        self.assertFalse(perm_owner_ops.has_object_permission(req_c1, None, unrelated))

        # Admin override still permitted
        req_admin = MockRequest(self.admin_user)
        self.assertTrue(perm_owner_admin.has_object_permission(req_admin, None, unrelated))
        self.assertTrue(perm_owner_ops.has_object_permission(req_admin, None, unrelated))

        # Operator override permitted only in IsOwnerOrAdminOrOperator
        req_op = MockRequest(self.operator_user)
        self.assertFalse(perm_owner_admin.has_object_permission(req_op, None, unrelated))
        self.assertTrue(perm_owner_ops.has_object_permission(req_op, None, unrelated))

    def test_explicit_owner_attribute_and_custom_predicate_ownership(self):
        """Regression (Finding 2): Validates explicit owner attribute and is_owned_by predicate."""
        class ExplicitOwnerResource:
            def __init__(self, owner):
                self.owner = owner

        class PredicateResource:
            def __init__(self, owner):
                self._owner = owner

            def is_owned_by(self, user):
                return user == self._owner

        res_owner = ExplicitOwnerResource(self.customer1)
        res_pred = PredicateResource(self.customer1)

        perm = IsOwnerOrAdmin()

        class MockRequest:
            def __init__(self, user):
                self.user = user

        req_c1 = MockRequest(self.customer1)
        req_c2 = MockRequest(self.customer2)

        # Owner has access
        self.assertTrue(perm.has_object_permission(req_c1, None, res_owner))
        self.assertTrue(perm.has_object_permission(req_c1, None, res_pred))

        # Non-owner is denied
        self.assertFalse(perm.has_object_permission(req_c2, None, res_owner))
        self.assertFalse(perm.has_object_permission(req_c2, None, res_pred))

