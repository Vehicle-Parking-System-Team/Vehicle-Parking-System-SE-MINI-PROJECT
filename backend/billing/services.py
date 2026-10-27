from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from rates.calculations import billable_hours

from .models import BillingReceipt


def _receipt_values(record):
    """Build stable receipt snapshots from a completed, billed session."""
    if (
        record.status != record.Status.COMPLETED
        or record.check_out_time is None
        or record.fee_amount is None
    ):
        raise ValidationError({
            'record_id': 'A receipt can only be generated for a checked-out session with a computed fee.'
        })

    if (
        record.check_out_time < record.check_in_time
        or record.hourly_rate_snapshot is None
        or record.grace_period_minutes_snapshot is None
    ):
        raise ValidationError({
            'record_id': 'The completed session is missing valid billing snapshots.'
        })

    elapsed = record.check_out_time - record.check_in_time
    duration_seconds = elapsed.days * 86400 + elapsed.seconds
    multiplier = record.vehicle_multiplier_snapshot
    if multiplier is None:
        # Sessions billed before multipliers were introduced used a multiplier of 1.
        multiplier = Decimal('1.00')

    return {
        'registration_number': (
            record.registration_number_snapshot or record.vehicle.registration_number
        ),
        'vehicle_type': (
            record.vehicle_type_at_checkin_snapshot or record.vehicle.vehicle_type
        ),
        'slot_number': record.slot_number_snapshot or record.slot.slot_number,
        'zone_name': record.zone_name_snapshot or record.slot.zone.name,
        'check_in_time': record.check_in_time,
        'check_out_time': record.check_out_time,
        'duration_seconds': duration_seconds,
        'billable_hours': billable_hours(
            elapsed, record.grace_period_minutes_snapshot,
        ),
        'hourly_rate': record.hourly_rate_snapshot,
        'vehicle_multiplier': multiplier,
        'grace_period_minutes': record.grace_period_minutes_snapshot,
        'fee_amount': record.fee_amount,
        'currency': 'INR',
    }


@transaction.atomic
def generate_receipt(record):
    """Create one receipt per completed record; repeats return the same receipt."""
    # Validate before querying/creating so an active or incomplete session is rejected.
    defaults = _receipt_values(record)
    receipt, created = BillingReceipt.objects.get_or_create(
        parking_record=record,
        defaults=defaults,
    )
    return receipt, created
