from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.db.transaction import TransactionManagementError
from django.test import TransactionTestCase

from common.exceptions import Conflict
from .models import ParkingSlot, ParkingZone
from . import services


class SlotStateTests(TransactionTestCase):
    def setUp(self):
        self.zone = ParkingZone.objects.create(name='Ground')
        self.slot = ParkingSlot.objects.create(zone=self.zone, slot_number='A-1')

    def test_checkin_and_checkout(self):
        with transaction.atomic():
            self.assertEqual(services.occupy_slot(self.slot.pk).status, 'occupied')
        with transaction.atomic():
            self.assertEqual(services.release_slot(self.slot.pk).status, 'available')

    def test_operations_require_caller_transaction(self):
        for hook in (services.occupy_slot, services.release_slot):
            with self.assertRaises(TransactionManagementError):
                hook(self.slot.pk)

    def test_failed_checkin_rolls_back_slot_and_other_writes(self):
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                services.occupy_slot(self.slot.pk)
                self.zone.description = 'Partial check-in write'
                self.zone.save()
                raise RuntimeError('Check-in record failed')
        self.slot.refresh_from_db()
        self.zone.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')
        self.assertEqual(self.zone.description, '')

    def test_failed_checkout_rolls_back_slot(self):
        ParkingSlot.objects.filter(pk=self.slot.pk).update(status='occupied')
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                services.release_slot(self.slot.pk)
                raise RuntimeError('Fee or checkout record failed')
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'occupied')

    def test_second_allocation_conflicts(self):
        with transaction.atomic():
            services.occupy_slot(self.slot.pk)
        with transaction.atomic(), self.assertRaises(Conflict):
            services.occupy_slot(self.slot.pk)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'occupied')

    def test_unavailable_states_cannot_be_allocated(self):
        for state in ('occupied', 'reserved', 'maintenance'):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=state)
            with self.subTest(state=state), transaction.atomic(), self.assertRaises(Conflict):
                services.occupy_slot(self.slot.pk)

    def test_inactive_slot_or_zone_cannot_be_allocated(self):
        for inactive_zone in (False, True):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(is_active=inactive_zone)
            ParkingZone.objects.filter(pk=self.zone.pk).update(is_active=not inactive_zone)
            with transaction.atomic(), self.assertRaises(Conflict):
                services.occupy_slot(self.slot.pk)

    def test_release_requires_occupied(self):
        for state in ('available', 'maintenance', 'reserved'):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=state)
            with transaction.atomic(), self.assertRaises(Conflict):
                services.release_slot(self.slot.pk)

    def test_maintenance_round_trip(self):
        self.assertEqual(services.set_maintenance(self.slot.pk, True).status, 'maintenance')
        self.assertEqual(services.set_maintenance(self.slot.pk, False).status, 'available')

    def test_repeated_maintenance_does_not_hide_a_stale_state(self):
        services.set_maintenance(self.slot.pk, True)
        with self.assertRaises(Conflict):
            services.set_maintenance(self.slot.pk, True)

    def test_unknown_database_errors_are_not_misreported_as_duplicates(self):
        with patch.object(ParkingSlot, 'save', side_effect=IntegrityError('unrelated failure')):
            with self.assertRaises(IntegrityError):
                services.create_slot({'zone': self.zone, 'slot_number': 'B-2', 'floor': 0})
