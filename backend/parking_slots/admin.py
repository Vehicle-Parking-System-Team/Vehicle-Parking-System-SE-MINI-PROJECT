from django.contrib import admin
from .models import ParkingSlot, ParkingZone


@admin.register(ParkingZone)
class ParkingZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_number', 'zone', 'status', 'vehicle_type', 'is_active')
    list_filter = ('status', 'zone', 'vehicle_type', 'is_active')
    search_fields = ('slot_number', 'zone__name')
    list_select_related = ('zone',)
