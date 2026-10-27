from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from parking_slots.permissions import CanManageParking

from .models import ParkingRecord

from .serializers import (
    CheckInRequestSerializer,
    CheckOutRequestSerializer,
    CheckOutRecordSerializer,
    ParkingHistoryQuerySerializer,
    ParkingHistoryRecordSerializer,
    ParkingRecordSerializer,
)
from .services import check_in_vehicle, check_out_vehicle


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


class VehicleCheckOutView(APIView):
    """Complete an active parking session and release its parking slot."""

    permission_classes = [IsAuthenticated, CanManageParking]

    def post(self, request):
        request_serializer = CheckOutRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        record = check_out_vehicle(
            registration_number=(
                request_serializer.validated_data["registration_number"]
            ),
            operator=request.user,
        )

        return Response(
            CheckOutRecordSerializer(record).data,
            status=status.HTTP_200_OK,
        )


class ParkingHistoryPagination(PageNumberPagination):
    """Bounded pagination for parking history."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ParkingHistoryView(APIView):
    """Read-only, paginated history of completed parking sessions."""

    permission_classes = [IsAuthenticated, CanManageParking]
    pagination_class = ParkingHistoryPagination

    def get(self, request):
        query_serializer = ParkingHistoryQuerySerializer(
            data=request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        filters = query_serializer.validated_data

        records = (
            ParkingRecord.objects
            .select_related("vehicle", "slot", "slot__zone", "operator")
            .filter(
                status=ParkingRecord.Status.COMPLETED,
                check_out_time__isnull=False,
            )
        )

        registration_number = filters.get("registration_number")
        if registration_number:
            records = records.filter(
                registration_number_snapshot=registration_number
            )

        vehicle_id = filters.get("vehicle_id")
        if vehicle_id is not None:
            records = records.filter(vehicle_id=vehicle_id)

        slot_id = filters.get("slot_id")
        if slot_id is not None:
            records = records.filter(slot_id=slot_id)

        start_date = filters.get("start_date")
        if start_date:
            records = records.filter(check_in_time__date__gte=start_date)

        end_date = filters.get("end_date")
        if end_date:
            records = records.filter(check_in_time__date__lte=end_date)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(records, request, view=self)
        serializer = ParkingHistoryRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
