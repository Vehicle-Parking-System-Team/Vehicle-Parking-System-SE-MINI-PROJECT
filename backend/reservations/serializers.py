from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from parking_slots.models import ParkingSlot
from vehicles.models import Vehicle
from .models import Reservation


class ReservationCreateSerializer(serializers.ModelSerializer):
    slot = serializers.PrimaryKeyRelatedField(queryset=ParkingSlot.objects.all())
    vehicle = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all())
    duration_minutes = serializers.IntegerField(min_value=1, max_value=1440, write_only=True)
    end_time = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
    customer = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'customer', 'vehicle', 'slot', 'start_time',
                  'duration_minutes', 'end_time', 'status', 'created_at']
        read_only_fields = ['id', 'customer', 'end_time', 'status', 'created_at']

    def validate(self, attrs):
        start = attrs['start_time']
        if start <= timezone.now():
            raise serializers.ValidationError({
                'start_time': 'Start time must be in the future.'
            })
        vehicle = attrs['vehicle']
        user = self.context['request'].user
        if user.role == 'Customer' and vehicle.owner_id != user.pk:
            raise serializers.ValidationError({
                'vehicle': 'Select a vehicle registered to your account.'
            })
        slot = attrs['slot']
        if not slot.is_active or not slot.zone.is_active:
            raise serializers.ValidationError({'slot': 'The parking slot is inactive.'})
        if slot.vehicle_type not in ('any', vehicle.vehicle_type):
            raise serializers.ValidationError({
                'slot': 'The slot does not support this vehicle type.'
            })
        if vehicle.owner.role != 'Customer' or not vehicle.owner.is_active or vehicle.owner.status != 'active':
            raise serializers.ValidationError({'vehicle': 'Vehicle owner must be an active customer.'})
        attrs['end_time'] = start + timedelta(minutes=attrs['duration_minutes'])
        return attrs

    def create(self, validated_data):
        from .services import create_reservation
        validated_data.pop('duration_minutes')
        return create_reservation(
            actor=self.context['request'].user,
            customer=validated_data['vehicle'].owner, **validated_data,
        )
