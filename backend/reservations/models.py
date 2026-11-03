from django.conf import settings
from django.db import models
from django.db.models import Q


class Reservation(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'Confirmed', 'Confirmed'
        CANCELLED = 'Cancelled', 'Cancelled'
        FULFILLED = 'Fulfilled', 'Fulfilled'

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='reservations',
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle', on_delete=models.PROTECT,
        related_name='reservations',
    )
    slot = models.ForeignKey(
        'parking_slots.ParkingSlot', on_delete=models.PROTECT,
        related_name='reservations',
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.CONFIRMED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=models.F('start_time')),
                name='reservation_positive_window',
            ),
        ]
        indexes = [
            models.Index(fields=['slot', 'status', 'start_time', 'end_time'],
                         name='reservation_slot_window'),
        ]
