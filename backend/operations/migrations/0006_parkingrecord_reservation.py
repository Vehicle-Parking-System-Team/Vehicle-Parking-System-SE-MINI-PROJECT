from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('operations', '0005_parkingrecord_vehicle_multiplier_snapshot'),
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='parkingrecord',
            name='reservation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='parking_records',
                to='reservations.reservation',
            ),
        ),
    ]
