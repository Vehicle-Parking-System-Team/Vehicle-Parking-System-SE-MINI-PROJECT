import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q


class BillingReceipt(models.Model):
    """Immutable receipt snapshots with an auditable payment settlement state."""

    class PaymentStatus(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        PAID = 'Paid', 'Paid'
        WAIVED = 'Waived', 'Waived'

    class PaymentMethod(models.TextChoices):
        CASH = 'Cash', 'Cash'
        CARD = 'Card', 'Card'
        UPI = 'UPI', 'UPI'

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

    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=4,
        choices=PaymentMethod.choices,
        null=True,
        blank=True,
    )
    payment_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    payment_timestamp = models.DateTimeField(null=True, blank=True)
    payment_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_parking_payments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.CheckConstraint(
                condition=Q(payment_amount__gte=0),
                name='billing_payment_amount_nonnegative',
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(payment_status='Paid')
                    | (
                        Q(payment_method__isnull=False)
                        & Q(payment_timestamp__isnull=False)
                        & Q(payment_amount=models.F('fee_amount'))
                    )
                ),
                name='billing_paid_payment_complete',
            ),
            models.CheckConstraint(
                condition=(
                    ~Q(payment_status='Waived')
                    | (
                        Q(payment_method__isnull=True)
                        & Q(payment_amount=Decimal('0.00'))
                    )
                ),
                name='billing_waived_payment_consistent',
            ),
        ]

    @property
    def invoice_number(self):
        raw = self.receipt_number
        hex_str = raw.hex if hasattr(raw, 'hex') else str(raw).replace('-', '')
        return f'INV-{hex_str.upper()}'

    def __str__(self):
        return f'{self.invoice_number} - {self.registration_number}'
