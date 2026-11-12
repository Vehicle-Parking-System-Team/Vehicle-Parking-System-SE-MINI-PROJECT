"""Shared read predicates for reservation-aware allocation and projections."""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Reservation


def walk_in_reservations(*, as_of=None):
    """Protect all unexpired confirmed windows plus their turnover buffer.

    Walk-ins have no departure time, so even a future arrival blocks allocation.
    Callers checking in a known vehicle may exclude that vehicle's own bookings.
    """
    as_of = as_of if as_of is not None else timezone.now()
    return Reservation.objects.filter(
        status=Reservation.Status.CONFIRMED,
        end_time__gt=as_of - timedelta(minutes=settings.RESERVATION_BUFFER_MINUTES),
    )
