from datetime import datetime, timezone

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ExistingDataMigrationTests(TransactionTestCase):
    def test_pr64_rows_survive_additive_floor_migration(self):
        executor = MigrationExecutor(connection)
        restore_targets = executor.loader.graph.leaf_nodes()
        before = [('parking_slots', '0001_initial')]
        after = [('parking_slots', '0002_parkingslot_floor')]
        executor.migrate(before)
        try:
            apps = executor.loader.project_state(before).apps
            Zone = apps.get_model('parking_slots', 'ParkingZone')
            Slot = apps.get_model('parking_slots', 'ParkingSlot')
            zones = [Zone.objects.create(name='North'), Zone.objects.create(
                name='South', description='Existing description', is_active=False,
            )]
            stamp = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
            for index, status in enumerate(['available', 'occupied', 'reserved', 'maintenance']):
                Slot.objects.create(
                    zone=zones[index % 2], slot_number=f'Bay-{index // 2}',
                    status=status, vehicle_type=['any', 'VAN', 'Compact', 'SUV'][index],
                    is_active=index != 3,
                )
            Zone.objects.update(created_at=stamp, updated_at=stamp)
            Slot.objects.update(created_at=stamp, updated_at=stamp)
            zone_rows = list(Zone.objects.order_by('pk').values())
            slot_rows = list(Slot.objects.order_by('pk').values())
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            apps = executor.loader.project_state(after).apps
            Zone = apps.get_model('parking_slots', 'ParkingZone')
            Slot = apps.get_model('parking_slots', 'ParkingSlot')
            self.assertEqual(list(Zone.objects.order_by('pk').values()), zone_rows)
            self.assertEqual(
                list(Slot.objects.order_by('pk').values(*slot_rows[0].keys())), slot_rows,
            )
            self.assertEqual(list(Slot.objects.values_list('floor', flat=True)), [None] * 4)
        finally:
            # Rewinding slots also rewinds dependent operations migrations.
            # Restore the complete graph so later tests see the current schema.
            MigrationExecutor(connection).migrate(restore_targets)
