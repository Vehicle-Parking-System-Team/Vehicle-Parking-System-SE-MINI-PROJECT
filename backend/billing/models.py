import uuid

from django.db import models


class BillingReceipt(models.Model):
    """Immutable receipt snapshots for completed parking sessions."""

    receipt_number = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    parking_record = models.OneToOneField(
        'operations.ParkingRecord',
        on_delete=models.PROTECT,
        related_name='billing_receipt',
    )
    registration_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=30)
    slot_number = models.CharField(max_length=100)
    zone_name = models.CharField(max_length=100)
    check_in_time = models.DateTimeField()
    check_out_time = models.DateTimeField()
    duration_seconds = models.PositiveBigIntegerField()
    billable_hours = models.PositiveIntegerField()
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    base_amount = models.DecimalField(max_digits=14, decimal_places=2)
    vehicle_multiplier = models.DecimalField(max_digits=5, decimal_places=2)
    multiplier_adjustment = models.DecimalField(max_digits=14, decimal_places=2)
    grace_period_minutes = models.PositiveIntegerField()
    fee_amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    @property
    def invoice_number(self):
        raw = self.receipt_number
        hex_str = raw.hex if hasattr(raw, 'hex') else str(raw).replace('-', '')
        return f'INV-{hex_str.upper()}'

    def __str__(self):
        return f'{self.invoice_number} - {self.registration_number}'
