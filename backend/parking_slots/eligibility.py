"""Privacy-safe reservation eligibility, evaluated in the slot-list query."""

from django.db.models import Exists, OuterRef

from reservations.queries import walk_in_reservations


def with_reservation_eligibility(queryset):
    return queryset.annotate(
        reservation_protected=Exists(walk_in_reservations().filter(slot_id=OuterRef('pk'))),
    )
