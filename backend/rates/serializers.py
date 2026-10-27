
from rest_framework import serializers

from rates.models import ParkingRate


class ParkingRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingRate
        fields = [
            'id',
            'vehicle_type',
            'hourly_rate',
            'vehicle_multiplier',
            'grace_period_minutes',
            'penalty_fee',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']

    def validate_hourly_rate(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'Hourly rate cannot be negative.'
            )
        return value

    def validate_vehicle_multiplier(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'Vehicle multiplier cannot be negative.'
            )
        return value

    def validate_penalty_fee(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'Penalty fee cannot be negative.'
            )
        return value
