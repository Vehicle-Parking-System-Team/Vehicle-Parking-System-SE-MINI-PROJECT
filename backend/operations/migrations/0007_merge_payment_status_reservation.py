from django.db import migrations


class Migration(migrations.Migration):
    """Join the original reservation and payment migration history."""

    dependencies = [
        ('operations', '0006_parkingrecord_reservation'),
        ('operations', '0006_parkingrecord_payment_status'),
    ]

    operations = []
