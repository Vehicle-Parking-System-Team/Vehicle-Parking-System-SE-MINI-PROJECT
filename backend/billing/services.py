from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from common.exceptions import Conflict
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
        multiplier = Decimal('1.00')

    hours = billable_hours(elapsed, record.grace_period_minutes_snapshot)
    base_amount = record.hourly_rate_snapshot * hours

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
        'billable_hours': hours,
        'hourly_rate': record.hourly_rate_snapshot,
        'base_amount': base_amount,
        'vehicle_multiplier': multiplier,
        'multiplier_adjustment': record.fee_amount - base_amount,
        'grace_period_minutes': record.grace_period_minutes_snapshot,
        'fee_amount': record.fee_amount,
        'currency': 'INR',
    }


@transaction.atomic
def generate_receipt(record):
    """Create one receipt per completed record; repeats return the same receipt."""
    defaults = _receipt_values(record)
    receipt, created = BillingReceipt.objects.get_or_create(
        parking_record=record,
        defaults=defaults,
    )
    return receipt, created


@transaction.atomic
def record_payment(receipt_number, operator, payment_status, payment_method=None,
                   payment_amount=Decimal('0.00')):
    """Atomically record settlement; paid and waived states cannot be reversed."""
    receipt = (
        BillingReceipt.objects.select_for_update()
        .filter(receipt_number=receipt_number)
        .first()
    )
    if receipt is None:
        raise NotFound('The requested receipt was not found.')

    if payment_amount < Decimal('0.00'):
        raise ValidationError({'payment_amount': 'Payment amount cannot be negative.'})

    if payment_status == BillingReceipt.PaymentStatus.PAID:
        if payment_method is None:
            raise ValidationError({
                'payment_method': 'A payment method is required for a paid bill.',
            })
        if payment_amount != receipt.fee_amount:
            raise ValidationError({
                'payment_amount': 'The recorded payment must exactly match the outstanding bill amount.',
            })
    elif payment_method is not None or payment_amount != Decimal('0.00'):
        raise ValidationError({
            'payment_amount': 'Pending and waived bills cannot record a collected amount or payment method.',
        })

    if receipt.payment_status != BillingReceipt.PaymentStatus.PENDING:
        same_settlement = (
            receipt.payment_status == payment_status
            and receipt.payment_method == payment_method
            and receipt.payment_amount == payment_amount
        )
        if same_settlement:
            return receipt, False
        raise Conflict(
            'A paid or waived bill is final and cannot be changed.',
        )

    receipt.payment_status = payment_status
    receipt.payment_method = payment_method
    receipt.payment_amount = payment_amount
    receipt.payment_recorded_by = operator

    if payment_status == BillingReceipt.PaymentStatus.PAID:
        receipt.payment_timestamp = timezone.now()
    else:
        receipt.payment_timestamp = None

    receipt.save(update_fields=[
        'payment_status', 'payment_method', 'payment_amount',
        'payment_timestamp', 'payment_recorded_by',
    ])
    return receipt, True
