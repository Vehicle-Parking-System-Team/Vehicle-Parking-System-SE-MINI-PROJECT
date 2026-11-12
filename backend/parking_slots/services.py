"""Slot lifecycle rules. Operations must call state hooks in their own transaction."""

from django.db import IntegrityError, connection, transaction
from django.db.transaction import TransactionManagementError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from common.exceptions import Conflict
from common.audit import record_audit_event
from .models import ParkingSlot, ParkingZone


PROTECTED_STATES = (ParkingSlot.Status.OCCUPIED, ParkingSlot.Status.RESERVED)


def _has_active_records(slot_ids):
    # Imported here because operations also consumes the slot state services.
    from operations.models import ParkingRecord

    return ParkingRecord.objects.filter(
        slot_id__in=slot_ids, status=ParkingRecord.Status.ACTIVE,
    ).exists()


def _has_future_confirmed_reservations(slot_ids):
    """Future windows only; expired, cancelled and fulfilled bookings do not block."""
    if not slot_ids:
        return False
    from reservations.models import Reservation

    return Reservation.objects.filter(
        slot_id__in=slot_ids,
        status=Reservation.Status.CONFIRMED,
        end_time__gt=timezone.now(),
    ).exists()


def _lock_slot(slot_id, new_zone_id=None):
    # Lock parents before children, also when a zone is deactivated or a bay moved.
    zone_id = get_object_or_404(ParkingSlot, pk=slot_id).zone_id
    zone_ids = {zone_id, new_zone_id} - {None}
    zones = {
        zone.pk: zone for zone in ParkingZone.objects.select_for_update()
        .filter(pk__in=zone_ids).order_by('pk')
    }
    slot = get_object_or_404(ParkingSlot.objects.select_for_update(), pk=slot_id)
    if slot.zone_id != zone_id:
        raise Conflict('This bay was moved. Refresh and try again.')
    slot.zone = zones[zone_id]
    return slot, zones


def _save_slot(slot):
    try:
        # Savepoint keeps the caller's transaction usable after a unique conflict.
        with transaction.atomic():
            slot.save()
    except IntegrityError:
        if ParkingSlot.objects.filter(
            zone_id=slot.zone_id, slot_number=slot.slot_number,
        ).exclude(pk=slot.pk).exists():
            raise ValidationError({
                'slot_number': 'This slot number already exists in this zone.'
            })
        raise
    return slot


@transaction.atomic
def create_slot(values):
    zone = get_object_or_404(
        ParkingZone.objects.select_for_update(), pk=values['zone'].pk,
    )
    if not zone.is_active:
        raise Conflict('Cannot add a bay to an inactive zone.')
    return _save_slot(ParkingSlot(**{**values, 'zone': zone}))


@transaction.atomic
def update_slot(slot_id, values):
    if 'status' in values:
        raise ValidationError({'status': 'Use the slot state services.'})
    target_zone = values.get('zone')
    slot, zones = _lock_slot(slot_id, target_zone.pk if target_zone else None)
    changed = any(getattr(slot, key) != value for key, value in values.items())
    protected = slot.status in PROTECTED_STATES or _has_active_records([slot.pk])
    if changed and _has_future_confirmed_reservations([slot.pk]):
        raise Conflict('This bay has a confirmed reservation and cannot be changed or deactivated.')
    if protected and (changed or values.get('is_active') is False):
        raise Conflict('A bay with an active record or occupied/reserved state cannot be changed or deactivated.')
    zone = zones[target_zone.pk] if target_zone else slot.zone
    if values.get('is_active', slot.is_active) and not zone.is_active:
        raise Conflict('Activate the zone before activating or changing this bay.')
    for key, value in values.items():
        setattr(slot, key, zone if key == 'zone' else value)
    return _save_slot(slot)


@transaction.atomic
def update_zone(zone_id, values, actor=None, request=None):
    zone = get_object_or_404(ParkingZone.objects.select_for_update(), pk=zone_id)
    previous_is_active = zone.is_active
    affected_slot_count = 0
    if values.get('is_active') is False:
        children = list(zone.slots.select_for_update().order_by('pk'))
        if _has_future_confirmed_reservations([slot.pk for slot in children]):
            raise Conflict('A zone with confirmed reservations cannot be deactivated.')
        if any(slot.status in PROTECTED_STATES for slot in children) or _has_active_records(
            [slot.pk for slot in children]
        ):
            raise Conflict('A zone with active records or occupied/reserved bays cannot be deactivated.')
        affected_slot_count = zone.slots.filter(is_active=True).update(
            is_active=False, updated_at=timezone.now(),
        )
    for key, value in values.items():
        setattr(zone, key, value)
    zone.save()
    if values.get('is_active') is False and (previous_is_active or affected_slot_count):
        record_audit_event(
            'parking_zone.deactivated', actor=actor, request=request,
            resource_type='parking_zone', resource_id=zone.pk,
            details={
                'previous_is_active': previous_is_active,
                'is_active': zone.is_active,
                'affected_slot_count': affected_slot_count,
            },
        )
    return zone


@transaction.atomic
def set_maintenance(slot_id, enabled, actor=None, request=None):
    slot, _ = _lock_slot(slot_id)
    expected = ParkingSlot.Status.AVAILABLE if enabled else ParkingSlot.Status.MAINTENANCE
    target = ParkingSlot.Status.MAINTENANCE if enabled else ParkingSlot.Status.AVAILABLE
    if enabled and _has_future_confirmed_reservations([slot.pk]):
        raise Conflict('A bay with confirmed reservations cannot enter maintenance.')
    slot = _transition(slot, expected, target)
    record_audit_event(
        'parking_slot.maintenance_changed', actor=actor, request=request,
        resource_type='parking_slot', resource_id=slot.pk,
        details={'previous_status': expected, 'status': slot.status},
    )
    return slot


def _transition(slot, expected, target):
    if not slot.is_active or not slot.zone.is_active:
        raise Conflict('This bay or its zone is inactive.')
    if _has_active_records([slot.pk]):
        raise Conflict('A bay with an active parking record cannot change state.')
    # Conditional write also prevents a stale reader from overwriting a winner.
    updated = ParkingSlot.objects.filter(
        pk=slot.pk, status=expected, is_active=True, zone__is_active=True,
    ).update(status=target, updated_at=timezone.now())
    if not updated:
        raise Conflict(f'This bay must be {expected} before it can become {target}.')
    slot.refresh_from_db()
    return slot


def _operation_transition(slot_id, expected, target):
    if not connection.in_atomic_block:
        raise TransactionManagementError(
            'Call slot state hooks inside the check-in/checkout transaction.'
        )
    with transaction.atomic():
        slot, _ = _lock_slot(slot_id)
        return _transition(slot, expected, target)


def occupy_slot(slot_id):
    """Call alongside creation of the active parking record; rollback together."""
    return _operation_transition(
        slot_id, ParkingSlot.Status.AVAILABLE, ParkingSlot.Status.OCCUPIED,
    )


def release_slot(slot_id):
    """Call after fee calculation and record completion in the same transaction."""
    return _operation_transition(
        slot_id, ParkingSlot.Status.OCCUPIED, ParkingSlot.Status.AVAILABLE,
    )
