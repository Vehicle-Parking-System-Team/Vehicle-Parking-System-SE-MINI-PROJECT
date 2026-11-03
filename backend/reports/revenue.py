"""Collected INR revenue from settled receipt snapshots (US-27)."""

from datetime import timedelta
from decimal import Decimal

from billing.models import BillingReceipt
from operations.models import ParkingRecord
from vehicles.models import Vehicle
from .serializers import REPORT_TIMEZONE


def _total():
    return {'receipt_count': 0, 'revenue': Decimal('0.00')}


def _add(total, count, revenue):
    total['receipt_count'] += count
    total['revenue'] += revenue


def _formatted(total):
    return {'receipt_count': total['receipt_count'], 'revenue': format(total['revenue'], '.2f')}


def revenue_report(*, start, end, interval='day', payment_method=None, vehicle_type=None):
    """Aggregate each paid receipt once, by payment time in [start, end)."""
    start = start.astimezone(REPORT_TIMEZONE)
    end = end.astimezone(REPORT_TIMEZONE)
    receipts = BillingReceipt.objects.filter(
        payment_status=BillingReceipt.PaymentStatus.PAID,
        payment_timestamp__gte=start, payment_timestamp__lt=end,
        parking_record__status=ParkingRecord.Status.COMPLETED,
        currency='INR',
    )
    if payment_method is not None:
        receipts = receipts.filter(payment_method=payment_method)
    if vehicle_type is not None:
        receipts = receipts.filter(vehicle_type=vehicle_type)

    total = _total()
    periods = {}
    methods = {value: _total() for value in BillingReceipt.PaymentMethod.values}
    vehicles = {value: _total() for value, _ in Vehicle.VEHICLE_TYPE_CHOICES}
    # Sum Decimal values in bounded batches: SQLite SUM uses binary floats,
    # which can lose cents on large totals. PostgreSQL follows the same rules.
    for paid_at, method, category, amount in receipts.order_by().values_list(
        'payment_timestamp', 'payment_method', 'vehicle_type', 'payment_amount',
    ).iterator(chunk_size=1000):
        key = paid_at.astimezone(REPORT_TIMEZONE).replace(minute=0, second=0, microsecond=0)
        if interval == 'day':
            key = key.replace(hour=0)
        _add(total, 1, amount)
        _add(periods.setdefault(key, _total()), 1, amount)
        _add(methods.setdefault(method, _total()), 1, amount)
        _add(vehicles.setdefault(category, _total()), 1, amount)

    # Include zero periods and clip the first/last bucket to the requested range.
    rows = []
    cursor = start
    while cursor < end:
        key = cursor.replace(minute=0, second=0, microsecond=0)
        if interval == 'day':
            key = key.replace(hour=0)
        stop = min(end, key + timedelta(hours=1) if interval == 'hour' else key + timedelta(days=1))
        rows.append({'start': cursor.isoformat(), 'end': stop.isoformat(),
                     **_formatted(periods.get(key, _total()))})
        cursor = stop

    return {
        'timezone': str(REPORT_TIMEZONE), 'currency': 'INR',
        'revenue_basis': 'collected_paid_receipts', 'date_basis': 'payment_timestamp',
        'vehicle_basis': 'receipt_snapshot', 'interval': interval,
        'start': start.isoformat(), 'end': end.isoformat(),
        'filters': {'payment_method': payment_method, 'vehicle_type': vehicle_type},
        'totals': _formatted(total), 'results': rows,
        'by_payment_method': [{'payment_method': key, **_formatted(value)}
                              for key, value in methods.items()],
        'by_vehicle_type': [{'vehicle_type': key, **_formatted(value)}
                            for key, value in vehicles.items()],
    }
