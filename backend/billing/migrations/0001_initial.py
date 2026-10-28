import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('operations', '0005_parkingrecord_vehicle_multiplier_snapshot'),
        ('rates', '0003_parkingrate_vehicle_multiplier'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt_number', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('registration_number', models.CharField(max_length=20)),
                ('vehicle_type', models.CharField(max_length=30)),
                ('slot_number', models.CharField(max_length=100)),
                ('zone_name', models.CharField(max_length=100)),
                ('check_in_time', models.DateTimeField()),
                ('check_out_time', models.DateTimeField()),
                ('duration_seconds', models.PositiveBigIntegerField()),
                ('billable_hours', models.PositiveIntegerField()),
                ('hourly_rate', models.DecimalField(decimal_places=2, max_digits=10)),
                ('base_amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('vehicle_multiplier', models.DecimalField(decimal_places=2, max_digits=5)),
                ('multiplier_adjustment', models.DecimalField(decimal_places=2, max_digits=14)),
                ('grace_period_minutes', models.PositiveIntegerField()),
                ('fee_amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parking_record', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='billing_receipt', to='operations.parkingrecord')),
            ],
            options={
                'ordering': ['-created_at', '-pk'],
            },
        ),
    ]
