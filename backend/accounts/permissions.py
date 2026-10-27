"""
Centralized Role-Based Access Control (RBAC) permissions for DRF.
Traceability: US-02 (#22), FR-16, NFR-SEC-01, NFR-SEC-02.
SRS Section 9.2, SAD Section 3.4.2 and Section 3.9.
"""

from django.contrib.auth import get_user_model
from rest_framework import permissions

ROLES = ('Admin', 'Operator', 'Customer')
ROLE_ADMIN = 'Admin'
ROLE_OPERATOR = 'Operator'
ROLE_CUSTOMER = 'Customer'


class BaseRolePermission(permissions.BasePermission):
    """
    Abstract base permission class enforcing persistent user roles and account status.

    Security guarantees:
    1. Rejects unauthenticated requests (causes DRF to return 401 Unauthorized).
    2. Rejects inactive, suspended, or deactivated accounts (403 Forbidden).
    3. Strictly checks database-persisted request.user.role against canonical roles.
    4. Denies access by default if role is missing, null, or unrecognized.
    5. Disregards any client-supplied role parameters in body, headers, or query strings.
    6. Fails closed (denies access) if allowed_roles is missing, empty, or misconfigured.
    """

    allowed_roles = ()
    message = 'You do not have permission to perform this action.'
    code = 'PERMISSION_DENIED'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False

        if not getattr(user, 'is_account_active', True):
            return False
        if getattr(user, 'status', 'active') != 'active':
            return False
        if not getattr(user, 'is_active', True):
            return False

        persisted_role = getattr(user, 'role', None)
        if not persisted_role or persisted_role not in ROLES:
            return False

        # Fail closed: misconfigured or empty allowed_roles must never grant access
        if not self.allowed_roles:
            return False

        if not all(r in ROLES for r in self.allowed_roles):
            return False

        return persisted_role in self.allowed_roles

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsAuthenticatedAndActive(BaseRolePermission):
    """Allows any authenticated user with an active account and recognized canonical role."""

    allowed_roles = ROLES


class IsAdmin(BaseRolePermission):
    """Strictly restricts access to users with the Admin (Administrator) role."""

    allowed_roles = (ROLE_ADMIN,)


class IsOperator(BaseRolePermission):
    """Strictly restricts access to users with the Operator role."""

    allowed_roles = (ROLE_OPERATOR,)


class IsCustomer(BaseRolePermission):
    """Strictly restricts access to users with the Customer role."""

    allowed_roles = (ROLE_CUSTOMER,)


class IsAdminOrOperator(BaseRolePermission):
    """Restricts access to administrative or operational staff (Admin or Operator)."""

    allowed_roles = (ROLE_ADMIN, ROLE_OPERATOR)


def has_roles(*roles):
    """
    Factory generating a BaseRolePermission subclass restricted to the specified roles.
    Example: permission_classes = [has_roles('Admin', 'Operator')]

    Fails closed on configuration errors:
    - Raises ValueError if no roles are provided.
    - Raises ValueError if any unsupported or invalid role is provided.
    """
    if not roles:
        raise ValueError('has_roles() requires at least one role to be specified.')

    invalid_roles = [r for r in roles if r not in ROLES]
    if invalid_roles:
        raise ValueError(
            f'Invalid role(s) specified in has_roles(): {invalid_roles}. '
            f'Supported canonical roles are: {ROLES}'
        )

    valid_roles = tuple(roles)

    class DynamicRolePermission(BaseRolePermission):
        allowed_roles = valid_roles

    DynamicRolePermission.__name__ = f'HasRoles_{"_".join(valid_roles)}'
    return DynamicRolePermission


def check_resource_ownership(user, obj):
    """
    Safely and explicitly verifies whether `user` owns the given `obj`.

    Ownership criteria:
    1. If `obj` is a User instance, ownership is true if obj == user.
    2. If `obj` provides an explicit `is_owned_by(user)` method, invoke it.
    3. If `obj` has an explicit `user` or `owner` attribute, match against user or user.id.
    4. Ambiguous or unrelated resources (e.g., matching IDs without an explicit owner attribute)
       are denied ownership by default.
    """
    if not user or not user.is_authenticated:
        return False

    UserModel = get_user_model()

    # Case 1: Resource is the User instance itself
    if isinstance(obj, UserModel):
        return obj == user or getattr(obj, 'pk', None) == getattr(user, 'pk', None)

    # Case 2: Explicit domain ownership predicate
    if callable(getattr(obj, 'is_owned_by', None)):
        return bool(obj.is_owned_by(user))

    # Case 3: Explicit owner or user attribute
    owner = getattr(obj, 'owner', None)
    if owner is None and hasattr(obj, 'user'):
        owner = getattr(obj, 'user', None)

    if owner is not None:
        if isinstance(owner, UserModel):
            return owner == user or getattr(owner, 'pk', None) == getattr(user, 'pk', None)
        owner_id = getattr(owner, 'id', getattr(owner, 'pk', owner))
        return owner_id == getattr(user, 'id', getattr(user, 'pk', None))

    # Default: Deny ownership for resources lacking explicit ownership relations
    return False


class IsOwnerOrAdmin(BaseRolePermission):
    """
    Object-level authorization:
    - Admin has full access to any resource.
    - Non-admin users are strictly restricted to resources they explicitly own.
    """

    allowed_roles = ROLES

    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False

        if getattr(request.user, 'role', None) == ROLE_ADMIN:
            return True

        return check_resource_ownership(request.user, obj)


class IsOwnerOrAdminOrOperator(BaseRolePermission):
    """
    Object-level authorization:
    - Admin and Operator have full access to manage the resource.
    - Customers are strictly restricted to resources they explicitly own.
    """

    allowed_roles = ROLES

    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False

        if getattr(request.user, 'role', None) in (ROLE_ADMIN, ROLE_OPERATOR):
            return True

        return check_resource_ownership(request.user, obj)
