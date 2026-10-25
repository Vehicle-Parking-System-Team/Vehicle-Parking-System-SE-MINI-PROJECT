import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def migrate_statuses_forward(apps, schema_editor):
    ParkingRecord = apps.get_model("operations", "ParkingRecord")

    ParkingRecord.objects.filter(status="active").update(
        status="ACTIVE"
    )
    ParkingRecord.objects.filter(status="completed").update(
        status="COMPLETED"
    )


def migrate_statuses_backward(apps, schema_editor):
    ParkingRecord = apps.get_model("operations", "ParkingRecord")

    ParkingRecord.objects.filter(status="ACTIVE").update(
        status="active"
    )
    ParkingRecord.objects.filter(status="COMPLETED").update(
        status="completed"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0001_initial"),
        ("parking_slots", "0002_parkingslot_floor"),
        ("vehicles", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ParkingSession",
            new_name="ParkingRecord",
        ),

        migrations.RenameField(
            model_name="parkingrecord",
            old_name="entry_time",
            new_name="check_in_time",
        ),

        migrations.AlterField(
            model_name="parkingrecord",
            name="check_in_time",
            field=models.DateTimeField(
                db_index=True,
                default=django.utils.timezone.now,
            ),
        ),

        migrations.RenameField(
            model_name="parkingrecord",
            old_name="exit_time",
            new_name="check_out_time",
        ),

        migrations.RenameField(
            model_name="parkingrecord",
            old_name="ticket_token",
            new_name="ticket_qr_token",
        ),

        migrations.RemoveConstraint(
            model_name="parkingrecord",
            name="unique_active_session_vehicle",
        ),

        migrations.RemoveConstraint(
            model_name="parkingrecord",
            name="unique_active_session_slot",
        ),

        migrations.RunPython(
            migrate_statuses_forward,
            migrate_statuses_backward,
        ),

        migrations.AlterField(
            model_name="parkingrecord",
            name="status",
            field=models.CharField(
                choices=[
                    ("ACTIVE", "Active"),
                    ("COMPLETED", "Completed"),
                ],
                db_index=True,
                default="ACTIVE",
                max_length=12,
            ),
        ),

        migrations.AlterField(
            model_name="parkingrecord",
            name="ticket_qr_token",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=512,
                null=True,
                unique=True,
            ),
        ),

        migrations.AlterField(
            model_name="parkingrecord",
            name="vehicle",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="parking_records",
                to="vehicles.vehicle",
            ),
        ),

        migrations.AlterField(
            model_name="parkingrecord",
            name="slot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="parking_records",
                to="parking_slots.parkingslot",
            ),
        ),

        migrations.AddField(
            model_name="parkingrecord",
            name="operator",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="parking_records",
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        migrations.AlterModelOptions(
            name="parkingrecord",
            options={
                "ordering": ["-check_in_time", "-pk"],
            },
        ),

        migrations.AddIndex(
            model_name="parkingrecord",
            index=models.Index(
                fields=["vehicle", "status"],
                name="ops_record_vehicle_status",
            ),
        ),

        migrations.AddConstraint(
            model_name="parkingrecord",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "ACTIVE")),
                fields=("vehicle",),
                name="uniq_active_record_vehicle",
            ),
        ),

        migrations.AddConstraint(
            model_name="parkingrecord",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "ACTIVE")),
                fields=("slot",),
                name="uniq_active_record_slot",
            ),
        ),
    ]