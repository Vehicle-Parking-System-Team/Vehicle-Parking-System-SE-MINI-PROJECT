import uuid

from django.db import models
from django.db.models import Q

from parking_slots.models import ParkingSlot
from vehicles.models import Vehicle


class ParkingSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name='parking_sessions',
    )

    slot = models.ForeignKey(
        ParkingSlot,
        on_delete=models.PROTECT,
        related_name='parking_sessions',
    )

    entry_time = models.DateTimeField(auto_now_add=True)

    exit_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    ticket_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    class Meta:
        ordering = ['-entry_time']
        constraints = [
            models.UniqueConstraint(
                fields=['vehicle'],
                condition=Q(status='active'),
                name='unique_active_session_vehicle',
            ),
            models.UniqueConstraint(
                fields=['slot'],
                condition=Q(status='active'),
                name='unique_active_session_slot',
            ),
        ]

    def __str__(self):
        return (
            f'{self.vehicle.registration_number} - '
            f'{self.slot} ({self.status})'
        )