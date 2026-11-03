
from rest_framework import generics
from django.db import transaction

from common.audit import record_audit_event

from rates.models import ParkingRate
from rates.permissions import IsAdminOrReadOnly
from rates.serializers import ParkingRateSerializer


def _rate_state(rate):
    return {
        'vehicle_type': rate.vehicle_type,
        'hourly_rate': str(rate.hourly_rate),
        'vehicle_multiplier': str(rate.vehicle_multiplier),
        'grace_period_minutes': rate.grace_period_minutes,
        'penalty_fee': str(rate.penalty_fee),
    }


class ParkingRateListCreateView(generics.ListCreateAPIView):
    """List configured parking rates or create a rate as an administrator."""

    queryset = ParkingRate.objects.all()
    serializer_class = ParkingRateSerializer
    permission_classes = [IsAdminOrReadOnly]

    @transaction.atomic
    def perform_create(self, serializer):
        rate = serializer.save()
        record_audit_event(
            'tariff.created', actor=self.request.user, request=self.request,
            resource_type='parking_rate', resource_id=rate.pk,
            details={'new_state': _rate_state(rate)},
        )


class ParkingRateDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a configured parking rate."""

    queryset = ParkingRate.objects.all()
    serializer_class = ParkingRateSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']

    @transaction.atomic
    def perform_update(self, serializer):
        # Snapshot under a lock; do not report a stale value read by get_object().
        rate = ParkingRate.objects.select_for_update().get(pk=serializer.instance.pk)
        serializer.instance = rate
        previous_state = _rate_state(rate)
        rate = serializer.save()
        new_state = _rate_state(rate)
        if new_state != previous_state:
            record_audit_event(
                'tariff.updated', actor=self.request.user, request=self.request,
                resource_type='parking_rate', resource_id=rate.pk,
                details={'previous_state': previous_state, 'new_state': new_state},
            )
