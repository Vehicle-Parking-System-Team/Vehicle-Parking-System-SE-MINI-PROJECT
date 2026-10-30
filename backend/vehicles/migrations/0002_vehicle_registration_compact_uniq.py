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


class Migration(migrations.Migration):
    dependencies = [
        ('vehicles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            reject_existing_compact_duplicates,
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
