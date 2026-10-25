"""Public, read-only slot availability (US-11 / FR-10)."""

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny

from vehicles.models import Vehicle
from .models import ParkingSlot


class AvailabilityFilterSerializer(serializers.Serializer):
    zone = serializers.IntegerField(min_value=1, required=False)
    vehicle_type = serializers.ChoiceField(
        choices=Vehicle.VEHICLE_TYPE_CHOICES, required=False,
    )


class AvailabilitySlotSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)
    zone_is_active = serializers.BooleanField(source='zone.is_active', read_only=True)

    class Meta:
        model = ParkingSlot
        # Deliberate allowlist: never expose records, plates, owners or tickets.
        fields = [
            'id', 'zone', 'zone_name', 'zone_is_active', 'slot_number',
            'floor', 'status', 'vehicle_type', 'is_active',
        ]
        read_only_fields = fields


@method_decorator(never_cache, name='dispatch')
class ParkingAvailabilityView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = AvailabilitySlotSerializer
    pagination_class = None

    def get_queryset(self):
        filters = AvailabilityFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        queryset = ParkingSlot.objects.select_related('zone').filter(
            is_active=True, zone__is_active=True,
        )
        for field, value in filters.validated_data.items():
            queryset = queryset.filter(**{field: value})
        return queryset.order_by('zone__name', 'floor', 'slot_number', 'pk')
