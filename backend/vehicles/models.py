from django.conf import settings
from django.db import models
from django.db.models.functions import Replace, Upper


class Vehicle(models.Model):
    """
    Vehicle entity adhering to SAD Section 4.1 and SRS Section 5.1.3 (FR-01 / US-05).
    Tracks vehicle license plates, categorized vehicle types, and user ownership.
    """

    VEHICLE_TYPE_TWO_WHEELER = 'Two-Wheeler'
    VEHICLE_TYPE_COMPACT = 'Compact'
    VEHICLE_TYPE_SUV = 'SUV'
    VEHICLE_TYPE_EV = 'EV Charging'

    VEHICLE_TYPE_CHOICES = [
        (VEHICLE_TYPE_TWO_WHEELER, 'Two-Wheeler'),
        (VEHICLE_TYPE_COMPACT, 'Compact'),
        (VEHICLE_TYPE_SUV, 'SUV'),
        (VEHICLE_TYPE_EV, 'EV Charging'),
    ]

    registration_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text='Normalized uppercase vehicle license plate or registration number.',
    )
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        help_text='Vehicle classification: Two-Wheeler, Compact, SUV, or EV Charging.',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vehicles',
        help_text='Authenticated user account owning the vehicle record.',
    )
    owner_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Contact name for the vehicle owner.',
    )
    owner_phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Contact phone number for the vehicle owner.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['registration_number'], name='vehicle_reg_idx'),
            models.Index(fields=['owner'], name='vehicle_owner_idx'),
        ]
        constraints = [
            # Registration formatting is not identity: spaces and hyphens are
            # presentation separators and must not allow duplicate vehicles.
            models.UniqueConstraint(
                Replace(
                    Replace(Upper('registration_number'), models.Value('-'), models.Value('')),
                    models.Value(' '),
                    models.Value(''),
                ),
                name='veh_reg_compact_uniq',
            ),
        ]

    def __str__(self):
        return f'{self.registration_number} ({self.vehicle_type})'

    @property
    def plate_number(self):
        """Alias for registration_number for SAD naming alignment."""
        return self.registration_number

    def clean(self):
        super().clean()
        if self.registration_number:
            self.registration_number = self.registration_number.strip().upper()

    def save(self, *args, **kwargs):
        if self.registration_number:
            self.registration_number = self.registration_number.strip().upper()
        super().save(*args, **kwargs)
