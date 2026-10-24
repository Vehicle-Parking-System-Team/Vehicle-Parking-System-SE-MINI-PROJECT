from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from parking_slots.permissions import CanManageParking

from .serializers import (
    CheckInRequestSerializer,
    ParkingSessionSerializer,
)
from .services import check_in_vehicle


class CheckInView(APIView):
    permission_classes = [IsAuthenticated, CanManageParking]

    def post(self, request):
        request_serializer = CheckInRequestSerializer(
            data=request.data,
        )
        request_serializer.is_valid(raise_exception=True)

        session = check_in_vehicle(
            registration_number=(
                request_serializer.validated_data["registration_number"]
            )
        )

        response_serializer = ParkingSessionSerializer(session)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )