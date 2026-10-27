from django.db import migrations, models


def populate_parking_snapshots(apps, schema_editor):
    """Backfill snapshot fields for parking records that already exist."""
    ParkingRecord = apps.get_model("operations", "ParkingRecord")
    database = schema_editor.connection.alias

    records = (
        ParkingRecord.objects.using(database)
        .select_related("vehicle", "slot__zone")
        .order_by("pk")
    )
    fields_to_update = [
        "registration_number_snapshot",
        "slot_number_snapshot",
        "vehicle_type_snapshot",
        "zone_name_snapshot",
    ]
    batch = []

    for record in records.iterator(chunk_size=500):
        record.registration_number_snapshot = record.vehicle.registration_number
        record.slot_number_snapshot = record.slot.slot_number
        record.vehicle_type_snapshot = record.vehicle.vehicle_type
        record.zone_name_snapshot = record.slot.zone.name
        batch.append(record)

        if len(batch) >= 500:
            ParkingRecord.objects.using(database).bulk_update(
                batch,
                fields_to_update,
                batch_size=500,
            )
            batch = []

    if batch:
        ParkingRecord.objects.using(database).bulk_update(
            batch,
            fields_to_update,
            batch_size=500,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0003_parkingrecord_fee_amount"),
    ]

    operations = [
        migrations.AddField(
            model_name="parkingrecord",
            name="registration_number_snapshot",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="parkingrecord",
            name="slot_number_snapshot",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="parkingrecord",
            name="vehicle_type_snapshot",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=30,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="parkingrecord",
            name="zone_name_snapshot",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=100,
                null=True,
            ),
        ),
        migrations.RunPython(
            populate_parking_snapshots,
            migrations.RunPython.noop,
        ),
    ]
