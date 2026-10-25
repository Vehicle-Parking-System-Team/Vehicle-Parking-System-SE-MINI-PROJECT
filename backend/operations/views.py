from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from parking_slots.permissions import CanManageParking

from .serializers import (
    CheckInRequestSerializer,
    ParkingRecordSerializer,
)
from .services import check_in_vehicle


class VehicleCheckInView(APIView):
    """Check in a vehicle and assign a compatible parking slot."""

    permission_classes = [IsAuthenticated, CanManageParking]

    def post(self, request):
        request_serializer = CheckInRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        record = check_in_vehicle(
            registration_number=(
                request_serializer.validated_data["registration_number"]
            ),
            operator=request.user,
            slot_id=request_serializer.validated_data.get("slot_id"),
        )

        return Response(
            ParkingRecordSerializer(record).data,
            status=status.HTTP_201_CREATED,
        )