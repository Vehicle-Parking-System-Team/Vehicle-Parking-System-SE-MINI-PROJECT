from django.db import IntegrityError
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import ParkingSlot, ParkingZone
from .serializers import ParkingSlotSerializer, ParkingZoneSerializer


class ParkingZoneListCreateView(generics.ListCreateAPIView):
    serializer_class = ParkingZoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ParkingZone.objects.all()


class ParkingZoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ParkingZoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ParkingZone.objects.all()

    def perform_destroy(self, instance):
        if instance.slots.exists():
            raise ValidationError({
                'detail': 'Remove the parking slots before deleting this zone.'
            })
        instance.delete()


class ParkingSlotListCreateView(generics.ListCreateAPIView):
    serializer_class = ParkingSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ParkingSlot.objects.select_related('zone').all()
        zone_id = self.request.query_params.get('zone')
        slot_status = self.request.query_params.get('status')

        if zone_id:
            queryset = queryset.filter(zone_id=zone_id)
        if slot_status:
            queryset = queryset.filter(status=slot_status)

        return queryset

    def perform_create(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError({
                'slot_number': 'This slot number already exists in this zone.'
            })


class ParkingSlotDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ParkingSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ParkingSlot.objects.select_related('zone').all()

    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError({
                'slot_number': 'This slot number already exists in this zone.'
            })


class ParkingSlotStatusView(generics.UpdateAPIView):
    serializer_class = ParkingSlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ParkingSlot.objects.all()
    http_method_names = ['patch', 'options', 'head']

    def patch(self, request, *args, **kwargs):
        slot = self.get_object()
        new_status = request.data.get('status')

        valid_statuses = ParkingSlot.Status.values
        if new_status not in valid_statuses:
            return Response(
                {'status': ['Choose a valid parking-slot status.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        slot.status = new_status
        slot.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(slot).data)
