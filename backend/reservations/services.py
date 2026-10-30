from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot
from operations.models import ParkingRecord
from vehicles.models import Vehicle
from .models import Reservation


@transaction.atomic
def create_reservation(*, actor, customer, vehicle, slot, start_time, end_time):
    # Lock vehicle BEFORE slot for every reservation writer. Concurrent requests
    # for the same vehicle on different slots must serialize on PostgreSQL.
    Vehicle.objects.select_for_update().get(pk=vehicle.pk)
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
        vehicle=vehicle, status=Reservation.Status.CONFIRMED,
        start_time__lt=end_time, end_time__gt=start_time,
    ).exists():
        raise Conflict('The vehicle already has a reservation for this time window.')
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


@transaction.atomic
def change_reservation(*, reservation_id, actor, cancel=False, start_time=None, end_time=None):
    """Lock vehicle, then slot, then reservation to serialize all writers."""
    from rest_framework.exceptions import NotFound, PermissionDenied

    try:
        original = Reservation.objects.only('slot_id', 'vehicle_id').get(
            pk=reservation_id,
        )
        reservation_slot_id = original.slot_id
        reservation_vehicle_id = original.vehicle_id
    except Reservation.DoesNotExist:
        raise NotFound('Reservation not found.')

    Vehicle.objects.select_for_update().get(pk=reservation_vehicle_id)
    locked_slot = ParkingSlot.objects.select_for_update().get(pk=reservation_slot_id)
    reservation = Reservation.objects.select_for_update().get(pk=reservation_id)
    if reservation.vehicle_id != reservation_vehicle_id:
        raise Conflict('Reservation vehicle changed concurrently; please retry.')
    if reservation.slot_id != locked_slot.pk:
        raise Conflict('Reservation changed concurrently; please retry.')
    if actor.role not in ('Admin', 'Operator', 'Customer'):
        raise PermissionDenied('Not authorized to manage reservations.')
    if actor.role == 'Customer' and reservation.customer_id != actor.pk:
        # Do not reveal the existence of another customer's reservation.
        raise NotFound('Reservation not found.')

    if reservation.status != Reservation.Status.CONFIRMED:
        raise serializers.ValidationError({
            'status': 'Only confirmed reservations may be changed or cancelled.'
        })
    if reservation.start_time <= timezone.now():
        raise serializers.ValidationError({
            'start_time': 'A reservation that has started cannot be changed or cancelled.'
        })
    # An early check-in must also block changes. Check the linked record,
    # not physical slot occupancy (which may belong to another vehicle).
    # Retain the guard after checkout: a commenced booking is never pending.
    if ParkingRecord.objects.filter(reservation=reservation).exists():
        raise serializers.ValidationError({
            'status': 'A checked-in reservation cannot be changed or cancelled.'
        })

    if cancel:
        reservation.status = Reservation.Status.CANCELLED
        reservation.save(update_fields=['status'])
        # Reservations hold a time window rather than changing slot.status.
        # Excluding Cancelled rows releases the slot immediately for rebooking.
        return reservation

    if start_time is None or end_time is None:
        raise serializers.ValidationError({
            'start_time': 'A new start time and duration are required.'
        })
    if start_time <= timezone.now() or end_time <= start_time:
        raise serializers.ValidationError({
            'start_time': 'New start time must be in the future and duration positive.'
        })
    if not locked_slot.is_active or not locked_slot.zone.is_active:
        raise Conflict('The selected slot is unavailable.')
    if locked_slot.status == ParkingSlot.Status.MAINTENANCE:
        raise Conflict('The selected slot is unavailable.')
    if Reservation.objects.filter(
        vehicle_id=reservation.vehicle_id,
        status=Reservation.Status.CONFIRMED,
        start_time__lt=end_time, end_time__gt=start_time,
    ).exclude(pk=reservation.pk).exists():
        raise Conflict('The vehicle already has a reservation for this time window.')
    if Reservation.objects.filter(
        slot=locked_slot, status=Reservation.Status.CONFIRMED,
        start_time__lt=end_time, end_time__gt=start_time,
    ).exclude(pk=reservation.pk).exists():
        raise Conflict('The selected slot is already reserved for this time window.')
    reservation.start_time = start_time
    reservation.end_time = end_time
    reservation.save(update_fields=['start_time', 'end_time'])
    return reservation
