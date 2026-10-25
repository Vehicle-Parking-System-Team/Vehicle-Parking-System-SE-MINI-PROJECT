from decimal import Decimal

from rest_framework import serializers
from rates.calculations import billable_hours, elapsed_microseconds
from vehicles.services import normalize_registration_number

from .models import ParkingRecord


class CheckInRequestSerializer(serializers.Serializer):
    registration_number = serializers.CharField(
        max_length=20,
        trim_whitespace=True,
    )
    slot_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )

    def validate_registration_number(self, value):
        plate = normalize_registration_number(value)

        if not plate:
            raise serializers.ValidationError(
                "A valid vehicle registration number is required."
            )

        return plate


class ParkingRecordSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.IntegerField(read_only=True)
    registration_number = serializers.CharField(
        source="vehicle.registration_number",
        read_only=True,
    )
    vehicle_type = serializers.CharField(
        source="vehicle.vehicle_type",
        read_only=True,
    )
    slot_id = serializers.IntegerField(read_only=True)
    slot_number = serializers.CharField(
        source="slot.slot_number",
        read_only=True,
    )
    zone_name = serializers.CharField(
        source="slot.zone.name",
        read_only=True,
    )
    operator_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ParkingRecord
        fields = [
            "id",
            "vehicle_id",
            "registration_number",
            "vehicle_type",
            "slot_id",
            "slot_number",
            "zone_name",
            "operator_id",
            "check_in_time",
            "check_out_time",
            "status",
            "ticket_qr_token",
        ]
        read_only_fields = fields


class CheckOutRequestSerializer(serializers.Serializer):
    registration_number = serializers.CharField(max_length=20, trim_whitespace=True)

    def validate(self, attrs):
        extra_fields = set(self.initial_data) - {'registration_number'}
        if extra_fields:
            raise serializers.ValidationError({field: 'This field is not accepted.' for field in extra_fields})
        return attrs


class CheckOutRecordSerializer(ParkingRecordSerializer):
    duration_seconds = serializers.SerializerMethodField()
    billable_hours = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    class Meta(ParkingRecordSerializer.Meta):
        fields = ParkingRecordSerializer.Meta.fields + [
            'duration_seconds', 'billable_hours', 'fee_amount', 'currency',
            'hourly_rate_snapshot', 'grace_period_minutes_snapshot', 'vehicle_type_snapshot',
        ]
        read_only_fields = fields

    def get_duration_seconds(self, record):
        elapsed = elapsed_microseconds(record.check_out_time - record.check_in_time)
        return format(Decimal(elapsed) / Decimal(1_000_000), '.6f')

    def get_billable_hours(self, record):
        return billable_hours(
            record.check_out_time - record.check_in_time, record.grace_period_minutes_snapshot,
        )

    def get_currency(self, record):
        return 'INR'
