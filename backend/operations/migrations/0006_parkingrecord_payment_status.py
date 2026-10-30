from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('operations', '0005_parkingrecord_vehicle_multiplier_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingrecord',
            name='payment_status',
            field=models.CharField(
                choices=[('Pending', 'Pending'), ('Paid', 'Paid'), ('Waived', 'Waived')],
                db_index=True,
                default='Pending',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='parkingrecord',
            name='payment_method',
            field=models.CharField(
                blank=True,
                choices=[('Cash', 'Cash'), ('Card', 'Card'), ('UPI', 'UPI')],
                max_length=4,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='parkingrecord',
            name='payment_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
        migrations.AddField(
            model_name='parkingrecord',
            name='payment_timestamp',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
