from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot
from .models import Reservation


@transaction.atomic
def create_reservation(*, actor, customer, vehicle, slot, start_time, end_time):
    # Serialize competing requests for the same slot on databases with row locks
    # (PostgreSQL). All reservation creation must use this service.
    locked_slot = ParkingSlot.objects.select_for_update().select_related('zone').get(pk=slot.pk)
    if start_time <= timezone.now() or end_time <= start_time:
        raise serializers.ValidationError({
            'start_time': 'Reservation must start in the future and end later.'
        })
    if not locked_slot.is_active or not locked_slot.zone.is_active:
        raise Conflict('The selected slot is unavailable.')
    if locked_slot.status in (ParkingSlot.Status.MAINTENANCE, ParkingSlot.Status.OCCUPIED):
        raise Conflict('The selected slot is unavailable.')
    if locked_slot.vehicle_type not in ('any', vehicle.vehicle_type):
        raise serializers.ValidationError({'slot': 'Incompatible vehicle type.'})
    if actor.role not in ('Customer', 'Operator'):
        raise serializers.ValidationError({'actor': 'Only customers or operators can create reservations.'})
    if actor.role == 'Customer' and actor.pk != customer.pk:
        raise serializers.ValidationError({'customer': 'Customers may only reserve for themselves.'})
    if customer.role != 'Customer' or not customer.is_active or customer.status != 'active':
        raise serializers.ValidationError({'customer': 'Reservation owner must be an active customer.'})
    if vehicle.owner_id != customer.pk:
        raise serializers.ValidationError({'vehicle': 'Vehicle does not belong to this customer.'})
    if Reservation.objects.filter(
        slot=locked_slot, status=Reservation.Status.CONFIRMED,
        start_time__lt=end_time, end_time__gt=start_time,
    ).exists():
        raise Conflict('The selected slot is already reserved for this time window.')
    return Reservation.objects.create(
        customer=customer, vehicle=vehicle, slot=locked_slot,
        start_time=start_time, end_time=end_time,
        status=Reservation.Status.CONFIRMED,
    )
