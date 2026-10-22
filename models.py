from django.db import models
from django.db.models.functions import Lower


class SlotStatus(models.TextChoices):
    """Single source of truth for slot state (US-10 / FR-04).
    Never compare against raw strings elsewhere; import this enum."""
    AVAILABLE = "AVAILABLE", "Available"
    OCCUPIED = "OCCUPIED", "Occupied"
    UNAVAILABLE = "UNAVAILABLE", "Unavailable"
    MAINTENANCE = "MAINTENANCE", "Maintenance"


class SlotType(models.TextChoices):
    # TODO(team): confirm the approved slot-type list before migrating.
    CAR = "CAR", "Car"
    BIKE = "BIKE", "Bike"
    LARGE = "LARGE", "Large vehicle"
    HANDICAPPED = "HANDICAPPED", "Handicapped"


class Slot(models.Model):
    """Minimum slot identity per blueprint: label, status, type.
    No zone/floor/section until the team approves them."""

    label = models.CharField(max_length=20)
    slot_type = models.CharField(max_length=20, choices=SlotType.choices)
    status = models.CharField(
        max_length=20, choices=SlotStatus.choices, default=SlotStatus.AVAILABLE
    )
    # Soft-remove: history (ParkingRecord, Reservation) may reference slots, so
    # DELETE deactivates instead of hard-deleting. Pending BR-07 / UD-03 approval.
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["label"]
        constraints = [
            # Case-insensitive unique label, enforced by the DB (not just the serializer).
            models.UniqueConstraint(Lower("label"), name="uniq_slot_label_ci"),
        ]

    def __str__(self):
        return f"{self.label} ({self.slot_type}, {self.status})"
