from django.shortcuts import render
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operations.models import ParkingRecord

from .models import BillingReceipt
from .serializers import (
    BillingReceiptSerializer,
    GenerateReceiptRequestSerializer,
)
from .services import generate_receipt


def _can_access_receipt(user, record):
    """Active admins/operators may assist; customers may read their own receipts."""
    if not getattr(user, 'is_authenticated', False):
        return False
    if not getattr(user, 'is_account_active', False):
        return False
    if user.role in ('Admin', 'Operator'):
        return True
    return user.role == 'Customer' and record.vehicle.owner_id == user.pk


def _get_receipt_or_404(receipt_number):
    receipt = (
        BillingReceipt.objects
        .select_related(
            'parking_record', 'parking_record__vehicle',
            'parking_record__slot', 'parking_record__slot__zone',
        )
        .filter(receipt_number=receipt_number)
        .first()
    )
    if receipt is None:
        raise NotFound('The requested receipt was not found.')
    return receipt


def _require_receipt_access(request, receipt):
    if not _can_access_receipt(request.user, receipt.parking_record):
        raise PermissionDenied('You do not have access to this receipt.')


class ReceiptCollectionView(APIView):
    """Generate (or idempotently return) a receipt for a completed session."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_serializer = GenerateReceiptRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        record = (
            ParkingRecord.objects
            .select_related('vehicle', 'slot', 'slot__zone')
            .filter(pk=request_serializer.validated_data['record_id'])
            .first()
        )
        if record is None:
            raise NotFound('The requested parking session was not found.')
        if not _can_access_receipt(request.user, record):
            raise PermissionDenied('You do not have access to this parking session.')

        receipt, created = generate_receipt(record)
        return Response(
            BillingReceiptSerializer(receipt, context={'request': request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ReceiptDetailView(APIView):
    """Return a receipt as structured API data."""

    permission_classes = [IsAuthenticated]

    def get(self, request, receipt_number):
        receipt = _get_receipt_or_404(receipt_number)
        _require_receipt_access(request, receipt)
        return Response(
            BillingReceiptSerializer(receipt, context={'request': request}).data,
        )


class ReceiptPrintableView(APIView):
    """Render a receipt using a printer-friendly HTML template."""

    permission_classes = [IsAuthenticated]

    def get(self, request, receipt_number):
        receipt = _get_receipt_or_404(receipt_number)
        _require_receipt_access(request, receipt)
        return render(request, 'billing/receipt.html', {'receipt': receipt})
