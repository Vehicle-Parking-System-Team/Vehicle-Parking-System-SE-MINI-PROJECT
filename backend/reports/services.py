"""Read-only reporting over canonical slots and parking records (US-26)."""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from operations.models import ParkingRecord
from parking_slots.models import ParkingZone
from .serializers import REPORT_TIMEZONE


def _number(value):
    return float(Decimal(str(value)).quantize(Decimal('0.01')))


def occupancy_report(*, start, end, interval='day', zone=None):
    """Use [start, end), clipped at one captured time, with current capacity."""
    as_of = timezone.now().astimezone(REPORT_TIMEZONE)
    start = start.astimezone(REPORT_TIMEZONE)
    end = end.astimezone(REPORT_TIMEZONE)
    observed_end = min(end, as_of)
    zones = ParkingZone.objects.order_by('pk')
    if zone is not None:
        zones = zones.filter(pk=zone)
        if not zones.exists():
            raise NotFound('Zone not found.')
    zones = list(zones.annotate(slot_count=Count('slots')).values('id', 'name', 'slot_count'))

    # Split at local hour boundaries even for daily reports, so peaks use the
    # same elapsed-time calculation and include sessions spanning midnight.
    hours = []
    cursor = start
    while cursor < end:
        step = timedelta(hours=1) - (cursor - cursor.replace(minute=0, second=0, microsecond=0))
        stop = end if end - cursor <= step else cursor + step
        hours.append((cursor, stop))
        cursor = stop

    periods = []
    hour_periods = []
    for hour_start, hour_end in hours:
        key = hour_start if interval == 'hour' else hour_start.date()
        if not periods or periods[-1]['key'] != key:
            periods.append({'key': key, 'start': hour_start, 'end': hour_end, 'seconds': 0})
        period = periods[-1]
        period['end'] = hour_end
        period['seconds'] += max(0, (min(hour_end, observed_end) - hour_start).total_seconds())
        hour_periods.append(len(periods) - 1)
    if len(periods) * len(zones) > 10000:
        raise ValidationError({'end': 'Request at most 10000 zone-period rows; narrow the range or select a zone.'})

    occupied = defaultdict(float)
    entries = defaultdict(int)
    clock_hours = defaultdict(float)
    if observed_end > start and zones:
        records = ParkingRecord.objects.filter(
            slot__zone_id__in=[item['id'] for item in zones],
            check_in_time__lt=observed_end,
        ).filter(Q(check_out_time__gt=start) | Q(check_out_time__isnull=True))
        for zone_id, entered, exited in records.values_list(
            'slot__zone_id', 'check_in_time', 'check_out_time',
        ).order_by().iterator(chunk_size=1000):
            entered = entered.astimezone(REPORT_TIMEZONE)
            exited = min(exited.astimezone(REPORT_TIMEZONE) if exited else as_of, observed_end)
            left = max(entered, start)
            if exited <= left:
                continue
            # Hours are contiguous; derive the first intersecting hour without
            # rescanning every earlier bucket for each record.
            first_hour = int((left.replace(minute=0, second=0, microsecond=0)
                              - start.replace(minute=0, second=0, microsecond=0)).total_seconds() // 3600)
            for index in range(first_hour, len(hours)):
                hour_start, hour_end = hours[index]
                if hour_start >= exited:
                    break
                seconds = (min(exited, hour_end) - max(left, hour_start)).total_seconds()
                period_index = hour_periods[index]
                occupied[zone_id, period_index] += seconds
                clock_hours[zone_id, hour_start.hour] += seconds
                if hour_start <= entered < hour_end:
                    entries[zone_id, period_index] += 1

    rows = []
    peaks = []
    for item in zones:
        zone_id = item['id']
        for index, period in enumerate(periods):
            seconds = occupied[zone_id, index]
            capacity_seconds = item['slot_count'] * period['seconds']
            rows.append({
                'zone_id': zone_id, 'zone_name': item['name'],
                'start': period['start'].isoformat(), 'end': period['end'].isoformat(),
                'slot_count': item['slot_count'], 'observed_minutes': _number(period['seconds'] / 60),
                'occupied_slot_minutes': _number(seconds / 60),
                'utilization_percent': _number(100 * seconds / capacity_seconds) if capacity_seconds else 0.0,
                'entries': entries[zone_id, index],
            })
        peak_seconds = max((clock_hours[zone_id, hour] for hour in range(24)), default=0)
        peaks.append({
            'zone_id': zone_id,
            'hours': [hour for hour in range(24) if peak_seconds > 0 and clock_hours[zone_id, hour] == peak_seconds],
            'occupied_slot_minutes': _number(peak_seconds / 60),
        })
    return {
        'timezone': str(REPORT_TIMEZONE), 'interval': interval,
        'start': start.isoformat(), 'end': end.isoformat(), 'as_of': as_of.isoformat(),
        'capacity_basis': 'current_total_slot_inventory',
        'zone_basis': 'current_slot_zone',
        'peak_hour_basis': 'occupied_slot_minutes_by_local_clock_hour',
        'results': rows, 'peak_hours': peaks,
    }
