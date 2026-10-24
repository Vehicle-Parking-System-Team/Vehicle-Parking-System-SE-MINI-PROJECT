from rest_framework import serializers
from .models import ParkingSlot, ParkingZone
from . import services
from vehicles.models import Vehicle


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

    def update(self, instance, validated_data):
        return services.update_zone(instance.pk, validated_data)


class ParkingSlotSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    zone_is_active = serializers.BooleanField(source='zone.is_active', read_only=True)
    floor = serializers.IntegerField(required=False, min_value=-2147483648, max_value=2147483647)
    vehicle_type = serializers.CharField(max_length=30, required=True)

    class Meta:
        model = ParkingSlot
        fields = [
            'id',
            'zone',
            'zone_name',
            'zone_is_active',
            'slot_number',
            'floor',
            'status',
            'vehicle_type',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
        # The existing database constraint remains the authority, including races.
        validators = []

    def validate(self, attrs):
        if 'status' in self.initial_data:
            raise serializers.ValidationError({
                'status': 'Status is managed by operations and the maintenance endpoint.'
            })
        if self.instance is None and 'floor' not in attrs:
            raise serializers.ValidationError({'floor': 'This field is required.'})
        return attrs

    def validate_vehicle_type(self, value):
        # Preserve existing PR #64 classifications until deliberately corrected.
        if self.instance and value == self.instance.vehicle_type:
            return value
        if value not in dict(Vehicle.VEHICLE_TYPE_CHOICES):
            raise serializers.ValidationError('Choose a supported vehicle type.')
        return value

    def create(self, validated_data):
        return services.create_slot(validated_data)

    def update(self, instance, validated_data):
        return services.update_slot(instance.pk, validated_data)

    def validate_zone(self, zone):
        if not zone.is_active and not (
            self.instance and self.instance.zone_id == zone.pk and not self.instance.is_active
        ):
            raise serializers.ValidationError(
                'Cannot assign a slot to an inactive parking zone.'
            )
        return zone
