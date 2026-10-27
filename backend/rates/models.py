
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class ParkingRate(models.Model):
    """
    Configurable parking tariff for a vehicle category.
    US-21: Configure parking rates.
    """

    VEHICLE_TYPE_CHOICES = [
        ('Two-Wheeler', 'Two-Wheeler'),
        ('Compact', 'Compact'),
        ('SUV', 'SUV'),
        ('EV Charging', 'EV Charging'),
    ]

    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        unique=True,
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    vehicle_multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(0)],
    )
    grace_period_minutes = models.PositiveIntegerField(default=15)
    penalty_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['vehicle_type']

    def __str__(self):
        return f'{self.vehicle_type}: {self.hourly_rate}/hour'
