import decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('billing', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='billingreceipt',
            name='payment_status',
            field=models.CharField(
                choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Waived', 'Waived')],
                db_index=True,
                default='Pending',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='billingreceipt',
            name='payment_method',
            field=models.CharField(
                blank=True,
                choices=[('Cash', 'Cash'), ('Card', 'Card'), ('UPI', 'UPI')],
                max_length=4,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='billingreceipt',
            name='payment_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=decimal.Decimal('0.00'),
                max_digits=14,
            ),
        ),
        migrations.AddField(
            model_name='billingreceipt',
            name='payment_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='billingreceipt',
            name='payment_recorded_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='recorded_parking_payments',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name='billingreceipt',
            constraint=models.CheckConstraint(
                condition=models.Q(('payment_amount__gte', 0)),
                name='billing_payment_amount_nonnegative',
            ),
        ),
        migrations.AddConstraint(
            model_name='billingreceipt',
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(('payment_status', 'Paid'))
                    | (
                        models.Q(('payment_method__isnull', False))
                        & models.Q(('payment_timestamp__isnull', False))
                        & models.Q(('payment_amount', models.F('fee_amount')))
                    )
                ),
                name='billing_paid_payment_complete',
            ),
        ),
        migrations.AddConstraint(
            model_name='billingreceipt',
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(('payment_status', 'Waived'))
                    | (
                        models.Q(('payment_method__isnull', True))
                        & models.Q(('payment_amount', decimal.Decimal('0.00')))
                    )
                ),
                name='billing_waived_payment_consistent',
            ),
        ),
    ]
