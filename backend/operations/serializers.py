from rest_framework import serializers

from .models import ParkingSession


class CheckInRequestSerializer(serializers.Serializer):
    registration_number = serializers.CharField(max_length=20)


class ParkingSessionSerializer(serializers.ModelSerializer):
    vehicle_registration = serializers.CharField(
        source="vehicle.registration_number",
        read_only=True,
    )
    slot_id = serializers.IntegerField(
        source="slot.pk",
        read_only=True,
    )
    slot_number = serializers.CharField(
        source="slot.slot_number",
        read_only=True,
    )
    zone_name = serializers.CharField(
        source="slot.zone.name",
        read_only=True,
    )

    class Meta:
        model = ParkingSession
        fields = [
            "id",
            "vehicle_registration",
            "slot_id",
            "slot_number",
            "zone_name",
            "entry_time",
            "status",
            "ticket_token",
        ]
        read_only_fields = fields