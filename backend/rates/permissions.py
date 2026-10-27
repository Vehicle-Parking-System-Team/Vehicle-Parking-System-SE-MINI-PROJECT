from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Active accounts may read parking rates.
    Only active administrators may create or update rates.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if not user.is_account_active:
            return False

        if request.method in SAFE_METHODS:
            return True

        return user.role == 'Admin'