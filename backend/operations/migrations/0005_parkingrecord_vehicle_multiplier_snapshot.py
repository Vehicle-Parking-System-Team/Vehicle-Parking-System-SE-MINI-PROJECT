from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('operations', '0004_parkingrecord_registration_number_snapshot_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingrecord',
            name='vehicle_multiplier_snapshot',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
            ),
        ),
    ]
