from rest_framework import serializers
from .models import ParkingSlot, ParkingZone


class ParkingZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingZone
        fields = [
            'id',
            'name',
            'description',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ParkingSlotSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)

    class Meta:
        model = ParkingSlot
        fields = [
            'id',
            'zone',
            'zone_name',
            'slot_number',
            'status',
            'vehicle_type',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_zone(self, zone):
        if not zone.is_active:
            raise serializers.ValidationError(
                'Cannot assign a slot to an inactive parking zone.'
            )
        return zone
