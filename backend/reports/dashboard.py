"""Current operational counters for the admin dashboard (US-25)."""

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Case, CharField, Count, Exists, F, OuterRef, Q, Value, When
from django.db.models.functions import TruncHour
from django.utils import timezone

from operations.models import ParkingRecord
from parking_slots.models import ParkingSlot
from .revenue import revenue_report
from .serializers import REPORT_TIMEZONE


def dashboard_metrics():
    as_of = timezone.now().astimezone(REPORT_TIMEZONE)
    start = as_of.replace(hour=0, minute=0, second=0, microsecond=0)
    active = ParkingRecord.objects.filter(status=ParkingRecord.Status.ACTIVE)
    # An active record takes precedence over a stale available/reserved flag.
    slots = ParkingSlot.objects.filter(is_active=True, zone__is_active=True).annotate(
        current_status=Case(
            When(Exists(active.filter(slot_id=OuterRef('pk'))),
                 then=Value(ParkingSlot.Status.OCCUPIED)),
            default='status', output_field=CharField(),
        ),
    ).order_by().values('zone_id', 'zone__name', 'current_status').annotate(count=Count('pk'))

    distribution = dict.fromkeys(ParkingSlot.Status.values, 0)
    zones = {}
    for row in slots:
        zone = zones.setdefault(row['zone_id'], {
            'zone_id': row['zone_id'], 'zone_name': row['zone__name'],
            'total_slots': 0, **dict.fromkeys(ParkingSlot.Status.values, 0),
        })
        status, count = row['current_status'], row['count']
        zone[status] += count
        zone['total_slots'] += count
        distribution[status] += count

    total_slots = sum(distribution.values())
    revenue = revenue_report(start=start, end=as_of, interval='hour')
    activity = [{'hour': hour, 'arrivals': 0, 'departures': 0, 'revenue': '0.00'} for hour in range(24)]
    records = ParkingRecord.objects.all()
    for field, key in (('check_in_time', 'arrivals'), ('check_out_time', 'departures')):
        rows = records.filter(**{f'{field}__gte': start, f'{field}__lt': as_of}).order_by().annotate(
            hour=TruncHour(field, tzinfo=REPORT_TIMEZONE),
        ).values('hour').annotate(count=Count('pk'))
        for row in rows:
            activity[row['hour'].hour][key] = row['count']
    for hour, row in enumerate(revenue['results']):
        activity[hour]['revenue'] = row['revenue']

    completed = records.filter(
        status=ParkingRecord.Status.COMPLETED, check_out_time__gte=start,
        check_out_time__lt=as_of,
    ).filter(check_out_time__gte=F('check_in_time')).aggregate(
        duration=Avg(F('check_out_time') - F('check_in_time')),
    )
    recent = records.filter(slot__is_active=True, slot__zone__is_active=True).aggregate(
        arrivals=Count('pk', filter=Q(
            check_in_time__gte=as_of - timedelta(hours=1), check_in_time__lt=as_of)),
        departures=Count('pk', filter=Q(
            check_out_time__gte=as_of - timedelta(hours=1), check_out_time__lt=as_of)),
    )
    # Simple pace estimates, not a trained forecast. Avoid extrapolating the
    # first hour's sparse revenue; cap parking demand at usable capacity.
    elapsed = Decimal(str((as_of - start).total_seconds()))
    projected_revenue = None
    if elapsed >= 3600:
        projected_revenue = format((Decimal(revenue['totals']['revenue']) * 86400 / elapsed).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP,
        ), '.2f')
    occupied = distribution['occupied']
    usable = total_slots - distribution['reserved'] - distribution['maintenance']
    next_hour = max(0, min(usable, occupied + recent['arrivals'] - recent['departures']))
    return {
        'as_of': as_of.isoformat(), 'timezone': str(REPORT_TIMEZONE),
        'capacity_basis': 'active_slots_in_active_zones',
        'total_slots': total_slots, 'free_slots': distribution['available'],
        'active_sessions': active.count(),
        'occupancy_percent': round(100 * distribution['occupied'] / total_slots, 2) if total_slots else 0.0,
        'slot_distribution': distribution,
        'zones': sorted(zones.values(), key=lambda zone: (zone['zone_name'], zone['zone_id'])),
        'today_revenue': revenue['totals']['revenue'],
        'currency': revenue['currency'], 'revenue_basis': revenue['revenue_basis'],
        'revenue_start': start.isoformat(), 'revenue_end': as_of.isoformat(),
        'activity': activity,
        'arrivals_today': sum(row['arrivals'] for row in activity),
        'departures_today': sum(row['departures'] for row in activity),
        'average_stay_minutes': round(completed['duration'].total_seconds() / 60, 1) if completed['duration'] is not None else None,
        'estimates': {
            'end_of_day_revenue': projected_revenue,
            'revenue_basis': 'today_collected_revenue / elapsed_seconds * 86400; available_after_first_hour',
            'next_hour_occupied_slots': next_hour,
            'occupancy_basis': 'current_occupied + last_60_minutes_arrivals - departures; bounded_to_usable_capacity',
            'recent_arrivals': recent['arrivals'], 'recent_departures': recent['departures'],
        },
    }
