"""
Centralized Role-Based Access Control (RBAC) permissions for DRF.
Traceability: US-02 (#22), FR-16, NFR-SEC-01, NFR-SEC-02.
SRS Section 9.2, SAD Section 3.4.2 and Section 3.9.
"""

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

        if self.allowed_roles:
            return persisted_role in self.allowed_roles

        return True

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsAuthenticatedAndActive(BaseRolePermission):
    """Allows any authenticated user with an active account and recognized role."""

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
    """
    valid_roles = tuple(r for r in roles if r in ROLES)

    class DynamicRolePermission(BaseRolePermission):
        allowed_roles = valid_roles

    DynamicRolePermission.__name__ = f'HasRoles_{"_".join(valid_roles)}'
    return DynamicRolePermission


class IsOwnerOrAdmin(BaseRolePermission):
    """
    Object-level authorization:
    - Admin has full access to any resource.
    - Non-admin users are restricted to resources they own.
    """

    allowed_roles = ROLES

    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False

        if getattr(request.user, 'role', None) == ROLE_ADMIN:
            return True

        owner = getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        if owner is not None:
            owner_id = getattr(owner, 'id', owner)
            return owner_id == request.user.id

        if obj == request.user or getattr(obj, 'id', None) == request.user.id:
            return True

        return False


class IsOwnerOrAdminOrOperator(BaseRolePermission):
    """
    Object-level authorization:
    - Admin and Operator have full access to manage the resource.
    - Customers are restricted to resources they own.
    """

    allowed_roles = ROLES

    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False

        if getattr(request.user, 'role', None) in (ROLE_ADMIN, ROLE_OPERATOR):
            return True

        owner = getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        if owner is not None:
            owner_id = getattr(owner, 'id', owner)
            return owner_id == request.user.id

        if obj == request.user or getattr(obj, 'id', None) == request.user.id:
            return True

        return False
