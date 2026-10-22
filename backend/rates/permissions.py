
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """Allow authenticated users to read rates; only Admin can modify them."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return True

        return (
            getattr(request.user, 'role', None) == 'Admin'
            and getattr(request.user, 'is_account_active', True)
        )
