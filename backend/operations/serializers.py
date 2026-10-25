
from rest_framework import serializers

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


class ParkingHistoryQuerySerializer(serializers.Serializer):
    registration_number = serializers.CharField(
        required=False,
        max_length=20,
        trim_whitespace=True,
    )
    vehicle_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    slot_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate_registration_number(self, value):
        plate = normalize_registration_number(value)

        if not plate:
            raise serializers.ValidationError(
                "A valid vehicle registration number is required."
            )

        return plate

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                "end_date": "End date must be on or after start date."
            })

        return attrs


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
            "fee_amount",
            "status",
            "ticket_qr_token",
        ]
        read_only_fields = fields


class ParkingHistoryRecordSerializer(serializers.ModelSerializer):
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
            "fee_amount",
            "status",
        ]
        read_only_fields = fields
