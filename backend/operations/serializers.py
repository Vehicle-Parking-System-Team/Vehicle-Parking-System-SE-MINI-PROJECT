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


class CheckOutRequestSerializer(serializers.Serializer):
    registration_number = serializers.CharField(
        max_length=20,
        trim_whitespace=True,
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

    duration_seconds = serializers.SerializerMethodField()

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
            "duration_seconds",
            "status",
            "ticket_qr_token",
        ]
        read_only_fields = fields

    def get_duration_seconds(self, obj):
        """
        Return the completed session duration in whole seconds.

        An active session has no final duration yet, so return None.
        """
        if obj.check_out_time is None:
            return None

        duration = (obj.check_out_time - obj.check_in_time).total_seconds()

        return max(0, int(duration))