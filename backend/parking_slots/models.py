from django.db import models


class ParkingZone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ParkingSlot(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        OCCUPIED = 'occupied', 'Occupied'
        RESERVED = 'reserved', 'Reserved'
        MAINTENANCE = 'maintenance', 'Maintenance'

    zone = models.ForeignKey(
        ParkingZone,
        on_delete=models.PROTECT,
        related_name='slots',
    )
    slot_number = models.CharField(max_length=30)
    # Historical PR #64 rows have no recorded floor; do not invent one.
    floor = models.IntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    vehicle_type = models.CharField(max_length=30, default='any')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['zone__name', 'slot_number']
        constraints = [
            models.UniqueConstraint(
                fields=['zone', 'slot_number'],
                name='unique_slot_number_per_zone',
            ),
        ]
        indexes = [
            models.Index(fields=['zone', 'status']),
        ]

    def __str__(self):
        return f'{self.zone.name} - {self.slot_number}'
