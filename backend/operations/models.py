from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class ParkingRecord(models.Model):
    """Persistent parking record for check-in, checkout, and history."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"

    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="parking_records",
    )

    slot = models.ForeignKey(
        "parking_slots.ParkingSlot",
        on_delete=models.PROTECT,
        related_name="parking_records",
    )

    reservation = models.ForeignKey(
        "reservations.Reservation",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="parking_records",
    )

    operator = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.PROTECT,
    related_name="parking_records",
    null=True,
    blank=True,
    )

    check_in_time = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    check_out_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    # Nullable so historical records are retained without inventing past charges.
    fee_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    hourly_rate_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vehicle_multiplier_snapshot = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grace_period_minutes_snapshot = models.PositiveIntegerField(null=True, blank=True)
    vehicle_type_snapshot = models.CharField(max_length=20, null=True, blank=True)
    vehicle_type_at_checkin_snapshot = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        editable=False,
    )
    registration_number_snapshot = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        editable=False,
    )
    slot_number_snapshot = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        editable=False,
    )
    zone_name_snapshot = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        editable=False,
    )

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    # Populated after the record receives its database ID.
    # Check-in will create the signed token within the same transaction.
    ticket_qr_token = models.CharField(
        max_length=512,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        ordering = ["-check_in_time", "-pk"]

        constraints = [
            models.UniqueConstraint(
                fields=["vehicle"],
                condition=Q(status="ACTIVE"),
                name="uniq_active_record_vehicle",
            ),
            models.UniqueConstraint(
                fields=["slot"],
                condition=Q(status="ACTIVE"),
                name="uniq_active_record_slot",
            ),
        ]

        indexes = [
            models.Index(
                fields=["vehicle", "status"],
                name="ops_record_vehicle_status",
            ),
        ]

    def __str__(self):
        registration_number = (
            self.registration_number_snapshot
            or self.vehicle.registration_number
        )
        return f"{registration_number} - {self.status}"
