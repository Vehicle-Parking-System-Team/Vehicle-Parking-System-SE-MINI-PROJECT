from django.contrib import admin

from .models import ParkingSlot, ParkingZone
from .permissions import can_manage_parking


class ParkingReadOnlyAdmin(admin.ModelAdmin):
    """Use the management API for writes so lifecycle rules cannot be bypassed."""

    def has_view_permission(self, request, obj=None):
        return can_manage_parking(request.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ParkingZone)
class ParkingZoneAdmin(ParkingReadOnlyAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(ParkingSlot)
class ParkingSlotAdmin(ParkingReadOnlyAdmin):
    list_display = ('slot_number', 'zone', 'floor', 'status', 'vehicle_type', 'is_active')
    list_filter = ('status', 'zone', 'floor', 'vehicle_type', 'is_active')
    search_fields = ('slot_number', 'zone__name')
    list_select_related = ('zone',)
