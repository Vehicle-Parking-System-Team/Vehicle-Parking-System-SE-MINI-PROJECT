
from django.contrib import admin

from rates.models import ParkingRate


@admin.register(ParkingRate)
class ParkingRateAdmin(admin.ModelAdmin):
    list_display = (
        'vehicle_type',
        'hourly_rate',
        'vehicle_multiplier',
        'grace_period_minutes',
        'penalty_fee',
        'updated_at',
    )
    list_filter = ('vehicle_type',)
    search_fields = ('vehicle_type',)
