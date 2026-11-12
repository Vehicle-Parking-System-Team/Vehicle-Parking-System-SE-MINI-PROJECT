from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from rates.calculations import billable_hours
from vehicles.services import filter_by_registration_number, normalize_registration_number
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.serializers import BillingReceiptSerializer
from billing.services import generate_receipt
from parking_slots.permissions import CanManageParking

from .models import ParkingRecord

from .serializers import (
    CheckInRequestSerializer,
    CheckoutPreviewQuerySerializer,
    CheckOutRequestSerializer,
    CheckOutRecordSerializer,
    ParkingHistoryQuerySerializer,
    ParkingHistoryRecordSerializer,
    ParkingRecordSerializer,
)
from .services import check_in_vehicle, check_out_vehicle, quote_checkout


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
            reservation_code=request_serializer.validated_data.get("reservation_code"),
        )

        return Response(
            ParkingRecordSerializer(record).data,
            status=status.HTTP_201_CREATED,
        )


class VehicleCheckOutView(APIView):
    """Complete an active parking session and release its parking slot."""

    permission_classes = [IsAuthenticated, CanManageParking]

    def get(self, request):
        query = CheckoutPreviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        records = ParkingRecord.objects.select_related('vehicle', 'slot').filter(
            status=ParkingRecord.Status.ACTIVE, check_out_time__isnull=True,
        )
        plate = query.validated_data.get('registration_number')
        if plate:
            records = filter_by_registration_number(
                records, normalize_registration_number(plate), 'vehicle__registration_number',
            )
        else:
            records = records.filter(slot__slot_number__iexact=query.validated_data['slot_number'])

        matches = list(records[:2])
        if not matches:
            raise NotFound('No active parking session matches that plate or bay.')
        if len(matches) > 1:
            raise ValidationError({'slot_number': 'Multiple zones use this bay number. Search by plate instead.'})

        record = matches[0]
        now = timezone.now()
        amount, rate, _ = quote_checkout(record, record.vehicle, now)
        duration = now - record.check_in_time
        return Response({
            'id': record.pk,
            'registration_number': record.vehicle.registration_number,
            'slot_number': record.slot_number_snapshot,
            'zone_name': record.zone_name_snapshot,
            'check_in_time': record.check_in_time,
            'duration_seconds': int(duration.total_seconds()),
            'billable_hours': billable_hours(duration, rate.grace_period_minutes),
            'hourly_rate': str(rate.hourly_rate),
            'vehicle_multiplier': str(rate.vehicle_multiplier),
            'grace_period_minutes': rate.grace_period_minutes,
            'fee_amount': str(amount),
            'currency': 'INR',
        })

    def post(self, request):
        request_serializer = CheckOutRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        # Checkout and receipt creation commit or roll back together.
        with transaction.atomic():
            record = check_out_vehicle(
                registration_number=(
                    request_serializer.validated_data["registration_number"]
                ),
                operator=request.user,
                expected_record_id=request_serializer.validated_data.get("expected_record_id"),
            )
            receipt, _ = generate_receipt(record)
            response_data = CheckOutRecordSerializer(record).data
            response_data["receipt"] = BillingReceiptSerializer(
                receipt, context={"request": request},
            ).data

        return Response(response_data, status=status.HTTP_200_OK)


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
            records = filter_by_registration_number(
                records, registration_number, 'registration_number_snapshot',
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
