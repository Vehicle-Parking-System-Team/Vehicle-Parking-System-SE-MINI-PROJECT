"""Compatibility step after main's checkout fee snapshot migration.

The checkout integration merged into main now creates fee_amount and the
billing snapshot fields. This migration remains in the US-20 chain so the
existing US-20 0004 migration filename and dependency are preserved.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0003_checkout_fee_snapshots"),
    ]

    operations = []
