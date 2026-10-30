from django.db import migrations


class Migration(migrations.Migration):
    """Join the two independently-added operations migrations on main.

    Keep the reservation branch first: Django reverses this dependency order.
    On SQLite, reversing the payment fields first prevents the table rebuild
    for the reservation FK from dropping payment_timestamp before its own
    RemoveField operation runs.
    """

    dependencies = [
        ('operations', '0006_parkingrecord_reservation'),
        ('operations', '0006_parkingrecord_payment_status'),
    ]

    operations = []
