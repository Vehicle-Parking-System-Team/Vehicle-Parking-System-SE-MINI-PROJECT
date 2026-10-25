"""Atomic fee processing and slot release required by US-10."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from common.exceptions import Conflict
from parking_slots.permissions import can_manage_parking
from parking_slots.services import release_slot
from rates.calculations import calculate_parking_fee
from rates.models import ParkingRate
from vehicles.models import Vehicle
from vehicles.services import normalize_registration_number
from .models import ParkingRecord


@transaction.atomic
def check_out_vehicle(registration_number, operator):
    if not can_manage_parking(operator):
        raise PermissionDenied('An active Admin or Operator account is required.')
    plate = normalize_registration_number(registration_number)
    if not plate or len(plate) > 20:
        raise ValidationError({'registration_number': 'Use a valid registration number.'})

    # Match check-in's vehicle-first order. Never lock a slot before its zone.
    vehicle = Vehicle.objects.select_for_update().filter(registration_number=plate).first()
    if vehicle is None:
        raise NotFound('No active parking record was found for this vehicle.')
    record = ParkingRecord.objects.select_for_update().filter(
        vehicle=vehicle, status=ParkingRecord.Status.ACTIVE,
    ).first()
    if record is None:
        raise NotFound('No active parking record was found for this vehicle.')
    if record.check_out_time is not None:
        raise Conflict('The active parking record already has a checkout timestamp.')

    rate = ParkingRate.objects.select_for_update().filter(vehicle_type=vehicle.vehicle_type).first()
    if rate is None:
        raise Conflict('Configure a parking rate for this vehicle type before checkout.')
    exit_time = timezone.now()
    amount = calculate_parking_fee(
        exit_time - record.check_in_time, rate.hourly_rate, rate.grace_period_minutes,
    )
    record.fee_amount = amount
    record.hourly_rate_snapshot = rate.hourly_rate
    record.grace_period_minutes_snapshot = rate.grace_period_minutes
    record.vehicle_type_snapshot = vehicle.vehicle_type
    record.check_out_time = exit_time
    record.status = ParkingRecord.Status.COMPLETED
    record.save(update_fields=[
        'fee_amount', 'hourly_rate_snapshot', 'grace_period_minutes_snapshot',
        'vehicle_type_snapshot', 'check_out_time', 'status',
    ])
    # The active-record guard now sees our completed record in this transaction.
    # A release failure rolls the fee, completion and timestamp back together.
    record.slot = release_slot(record.slot_id)
    record.vehicle = vehicle
    return record
