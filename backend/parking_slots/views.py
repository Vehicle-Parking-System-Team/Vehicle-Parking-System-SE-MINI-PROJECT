from rest_framework import generics, serializers
from rest_framework.response import Response

from .models import ParkingSlot, ParkingZone
from .permissions import CanManageParking
from .serializers import ParkingSlotSerializer, ParkingZoneSerializer
from . import services


class ParkingZoneListCreateView(generics.ListCreateAPIView):
    serializer_class = ParkingZoneSerializer
    permission_classes = [CanManageParking]
    queryset = ParkingZone.objects.all()


class ParkingZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ParkingZoneSerializer
    permission_classes = [CanManageParking]
    queryset = ParkingZone.objects.all()

    def perform_destroy(self, instance):
        services.update_zone(instance.pk, {'is_active': False})


class ParkingSlotListCreateView(generics.ListCreateAPIView):
    serializer_class = ParkingSlotSerializer
    permission_classes = [CanManageParking]

    def get_queryset(self):
        queryset = ParkingSlot.objects.select_related('zone').all()
        zone_id = self.request.query_params.get('zone')
        slot_status = self.request.query_params.get('status')
        if zone_id:
            try:
                zone_id = int(zone_id)
            except ValueError:
                raise serializers.ValidationError({'zone': 'Use an integer zone ID.'})
            queryset = queryset.filter(zone_id=zone_id)
        if slot_status:
            if slot_status not in ParkingSlot.Status.values:
                raise serializers.ValidationError({'status': 'Choose a valid slot status.'})
            queryset = queryset.filter(status=slot_status)
        return queryset


class ParkingSlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ParkingSlotSerializer
    permission_classes = [CanManageParking]
    queryset = ParkingSlot.objects.select_related('zone').all()

    def perform_destroy(self, instance):
        services.update_slot(instance.pk, {'is_active': False})


class MaintenanceSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        ParkingSlot.Status.AVAILABLE, ParkingSlot.Status.MAINTENANCE,
    ])


class ParkingSlotStatusView(generics.GenericAPIView):
    """Retain PR #64's route, restricting manual transitions to maintenance."""

    serializer_class = MaintenanceSerializer
    permission_classes = [CanManageParking]
    queryset = ParkingSlot.objects.all()
    http_method_names = ['patch', 'options', 'head']

    def patch(self, request, *args, **kwargs):
        slot = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot = services.set_maintenance(
            slot.pk, serializer.validated_data['status'] == ParkingSlot.Status.MAINTENANCE,
        )
        return Response(ParkingSlotSerializer(slot).data)
