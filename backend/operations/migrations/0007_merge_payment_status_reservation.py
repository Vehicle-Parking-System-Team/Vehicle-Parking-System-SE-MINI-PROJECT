from django.db import migrations


class Migration(migrations.Migration):
    """Join the two independently-added operations migrations on main."""

    dependencies = [
        ('operations', '0006_parkingrecord_payment_status'),
        ('operations', '0006_parkingrecord_reservation'),
    ]

    operations = []
