import re

from django.db import migrations, models
from django.db.models import Value
from django.db.models.functions import Replace, Upper


def reject_existing_compact_duplicates(apps, schema_editor):
    """
    Fail safely if legacy rows differ only by case/space/hyphen formatting.
    Do not delete or silently merge vehicle records during a migration.
    """
    Vehicle = apps.get_model('vehicles', 'Vehicle')
    database = schema_editor.connection.alias
    seen = {}
    collisions = []

    for vehicle in Vehicle.objects.using(database).only('pk', 'registration_number').iterator():
        key = re.sub(r'[- ]', '', vehicle.registration_number.strip().upper())
        previous_id = seen.get(key)
        if previous_id is not None:
            collisions.append((key, previous_id, vehicle.pk))
        else:
            seen[key] = vehicle.pk

    if collisions:
        sample = '; '.join(
            f'{key}: vehicle IDs {first_id} and {second_id}'
            for key, first_id, second_id in collisions[:10]
        )
        raise RuntimeError(
            'Cannot add compact vehicle-registration uniqueness: existing records '
            f'collide after separator normalization. Resolve these records first: {sample}'
        )


def normalize_legacy_registration_formats(apps, schema_editor):
    """
    Canonicalize rows that were valid under the previous separator-tolerant
    format. Compact display forms remain compact; mixed/space separators become
    hyphens. Invalid legacy values are left untouched for explicit cleanup.
    """
    Vehicle = apps.get_model('vehicles', 'Vehicle')
    database = schema_editor.connection.alias
    legacy_pattern = re.compile(
        r'^(?:[A-Z]{2}[-\s]?(?:[0-9]{1,2}[-\s]?)?[A-Z]{1,8}[-\s]?[0-9]{1,4}|[0-9]{2}[-\s]?BH[-\s]?[0-9]{4}[-\s]?[A-Z]{1,2})$'
    )

    for vehicle in Vehicle.objects.using(database).only('pk', 'registration_number').iterator():
        raw = vehicle.registration_number.strip().upper()
        if legacy_pattern.fullmatch(raw):
            canonical = re.sub(r'[-\s]+', '-', raw)
            if canonical != vehicle.registration_number:
                Vehicle.objects.using(database).filter(pk=vehicle.pk).update(
                    registration_number=canonical
                )


class Migration(migrations.Migration):
    dependencies = [
        ('vehicles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            reject_existing_compact_duplicates,
            migrations.RunPython.noop,
        ),
        migrations.RunPython(
            normalize_legacy_registration_formats,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name='vehicle',
            constraint=models.UniqueConstraint(
                Replace(
                    Replace(Upper('registration_number'), Value('-'), Value('')),
                    Value(' '),
                    Value(''),
                ),
                name='veh_reg_compact_uniq',
            ),
        ),
    ]
