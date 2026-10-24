from rest_framework.permissions import BasePermission


def can_manage_parking(user):
    return bool(
        user and user.is_authenticated and user.is_account_active
        and user.role in ('Admin', 'Operator')
    )


class CanManageParking(BasePermission):
    message = 'An active Admin or Operator account is required.'

    def has_permission(self, request, view):
        return can_manage_parking(request.user)
