"""Best-effort alerts, isolated from parking transactions and deduplicated in SQL."""

import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from accounts.models import User
from operations.models import ParkingRecord
from parking_slots.models import ParkingSlot
from reservations.models import Reservation
from .models import Notification

logger = logging.getLogger(__name__)


def _attempt(action):
    try:
        # A failed insert must not poison an enclosing transaction.
        with transaction.atomic():
            action()
    except Exception:
        logger.warning('In-app notification dispatch failed; operational changes are retained.')


def _parking_event(kind, record_id):
    record = ParkingRecord.objects.select_related('vehicle').get(pk=record_id)
    if kind == 'facility_full':
        slots = ParkingSlot.objects.filter(is_active=True, zone__is_active=True)
        if not slots.exists() or slots.filter(status=ParkingSlot.Status.AVAILABLE).exists():
            return
        # Concurrent final arrivals share the same full-capacity event key.
        latest = ParkingRecord.objects.filter(
            status=ParkingRecord.Status.ACTIVE, slot__is_active=True, slot__zone__is_active=True,
        ).order_by('-pk').values_list('pk', flat=True).first()
        key = f'facility-full:{latest}'
        recipients = User.objects.filter(role__in=['Admin', 'Operator'], is_active=True, status='active').values_list('pk', flat=True)
        message = 'Parking facility reached full capacity: no active spaces were available.'
    else:
        key = f'checkout:{record.pk}'
        recipients = User.objects.filter(pk=record.vehicle.owner_id, is_active=True, status='active').values_list('pk', flat=True)
        message = f'Checkout confirmed for {record.registration_number_snapshot or record.vehicle.registration_number}. Your parking session is complete.'
    Notification.objects.bulk_create([
        Notification(recipient_id=pk, kind=kind, event_key=key, message=message) for pk in recipients
    ], ignore_conflicts=True)


def schedule_parking_notification(kind, record_id):
    # Rolled-back operations never dispatch. Notification errors cannot undo a
    # successful checkout/receipt or check-in, including nested transactions.
    transaction.on_commit(lambda: _attempt(lambda: _parking_event(kind, record_id)), robust=True)


def notify_expiring_reservations(user):
    """Refresh only this user's expiry warnings when their inbox is polled."""
    def dispatch():
        now = timezone.now()
        reservations = Reservation.objects.filter(
            customer=user, status=Reservation.Status.CONFIRMED,
            end_time__gt=now, end_time__lte=now + timedelta(minutes=15),
        ).values_list('pk', 'end_time')
        Notification.objects.bulk_create([
            Notification(recipient=user, kind='reservation_expiring',
                         event_key=f'reservation-expiring:{pk}:{end.isoformat()}',
                         message=f'Reservation RES-{pk} expires at {end.astimezone(ZoneInfo("Asia/Kolkata")):%d %b %Y, %H:%M} IST.')
            for pk, end in reservations
        ], ignore_conflicts=True)
    _attempt(dispatch)
