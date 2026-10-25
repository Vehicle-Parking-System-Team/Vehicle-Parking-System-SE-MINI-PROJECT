from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections, transaction
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from rest_framework.test import APIClient

from common.exceptions import Conflict
from operations.models import ParkingRecord
from operations.services import check_in_vehicle
from vehicles.models import Vehicle
from .models import ParkingSlot, ParkingZone
from . import services


class ActiveRecordIntegrityTests(TestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(username='operator', role='Operator')
        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)
        self.zone = ParkingZone.objects.create(name='Zone A')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='A-01', floor=0, vehicle_type='Compact',
        )
        self.vehicle = Vehicle.objects.create(
            registration_number='KA01AB1234', vehicle_type='Compact', owner=self.operator,
        )
        self.record = ParkingRecord.objects.create(vehicle=self.vehicle, slot=self.slot)
        self.slot_url = f'/api/parking/slots/{self.slot.pk}/'

    def test_active_record_blocks_destructive_changes_despite_available_status(self):
        for method, values in (
            ('delete', {}), ('patch', {'is_active': False}), ('patch', {'floor': 2}),
            ('put', {'slot_number': 'Changed', 'zone': self.zone.pk, 'floor': 1, 'vehicle_type': 'SUV'}),
        ):
            with self.subTest(method=method, values=values):
                response = getattr(self.client, method)(self.slot_url, values, format='json')
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.data['code'], 'CONFLICT')
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_active)
        self.assertEqual(self.slot.floor, 0)
        self.assertEqual(self.slot.slot_number, 'A-01')

    def test_zone_deactivation_cannot_hide_an_active_record(self):
        other = ParkingSlot.objects.create(zone=self.zone, slot_number='A-02')
        url = f'/api/parking/zones/{self.zone.pk}/'
        for method in ('delete', 'patch', 'put'):
            response = getattr(self.client, method)(url, {
                'name': self.zone.name, 'is_active': False,
            }, format='json')
            self.assertEqual(response.status_code, 409)
        self.zone.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(self.zone.is_active)
        self.assertTrue(other.is_active)

    def test_manual_maintenance_cannot_override_active_record(self):
        for status in ('available', 'occupied', 'maintenance'):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=status)
            for target in ('maintenance', 'available'):
                response = self.client.patch(self.slot_url + 'status/', {'status': target})
                self.assertEqual(response.status_code, 409)
            self.slot.refresh_from_db()
            self.assertEqual(self.slot.status, status)

    def test_operations_cannot_release_slot_while_record_is_active(self):
        ParkingSlot.objects.filter(pk=self.slot.pk).update(status='occupied')
        with transaction.atomic(), self.assertRaises(Conflict):
            services.release_slot(self.slot.pk)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'occupied')

    def test_stale_available_slot_cannot_be_allocated_twice(self):
        second = Vehicle.objects.create(
            registration_number='KA01AB5678', vehicle_type='Compact', owner=self.operator,
        )
        response = self.client.post('/api/parking/check-in/', {
            'registration_number': second.registration_number, 'slot_id': self.slot.pk,
        })
        self.assertEqual(response.status_code, 409)
        self.assertEqual(ParkingRecord.objects.count(), 1)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')

    def test_completed_history_allows_soft_deactivation_and_is_retained(self):
        self.record.status = ParkingRecord.Status.COMPLETED
        self.record.save(update_fields=['status'])
        self.assertEqual(self.client.delete(self.slot_url).status_code, 204)
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_active)
        self.assertTrue(ParkingRecord.objects.filter(pk=self.record.pk).exists())

    def test_maintenance_slot_rejected_by_real_check_in(self):
        self.record.delete()
        ParkingSlot.objects.filter(pk=self.slot.pk).update(status='maintenance')
        response = self.client.post('/api/parking/check-in/', {
            'registration_number': self.vehicle.registration_number, 'slot_id': self.slot.pk,
        })
        self.assertEqual(response.status_code, 409)
        self.assertFalse(ParkingRecord.objects.exists())

    def test_failed_ticket_creation_rolls_back_real_check_in_and_slot(self):
        self.record.delete()
        with patch('operations.services.create_signed_ticket', side_effect=RuntimeError('test failure')):
            with self.assertRaises(RuntimeError):
                check_in_vehicle(self.vehicle.registration_number, self.operator, self.slot.pk)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')
        self.assertFalse(ParkingRecord.objects.exists())


@skipUnlessDBFeature('has_select_for_update')
class SlotConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(username='operator', role='Operator')
        self.zone = ParkingZone.objects.create(name='Zone A')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='A-01', floor=0, vehicle_type='Compact',
        )
        self.vehicles = [Vehicle.objects.create(
            registration_number=f'KA01AB123{index}', vehicle_type='Compact', owner=self.operator,
        ) for index in range(2)]

    def race(self, *actions):
        barrier = Barrier(len(actions))

        def run(action):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                action()
                return 'success'
            except Conflict:
                return 'conflict'
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            futures = [pool.submit(run, action) for action in actions]
            return [future.result(timeout=30) for future in futures]

    def check_in(self, index=0):
        return check_in_vehicle(
            self.vehicles[index].registration_number, self.operator, self.slot.pk,
        )

    def test_two_manual_allocations_have_exactly_one_winner(self):
        results = self.race(lambda: self.check_in(0), lambda: self.check_in(1))
        self.assertCountEqual(results, ['success', 'conflict'])
        self.assertEqual(ParkingRecord.objects.filter(slot=self.slot, status='ACTIVE').count(), 1)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'occupied')

    def test_check_in_and_deactivation_cannot_both_succeed(self):
        results = self.race(self.check_in, lambda: services.update_slot(self.slot.pk, {'is_active': False}))
        self.assertCountEqual(results, ['success', 'conflict'])
        self.slot.refresh_from_db()
        if results[0] == 'success':
            self.assertTrue(self.slot.is_active)
            self.assertEqual(self.slot.status, 'occupied')
            self.assertEqual(ParkingRecord.objects.count(), 1)
        else:
            self.assertFalse(self.slot.is_active)
            self.assertFalse(ParkingRecord.objects.exists())

    def test_check_in_and_maintenance_cannot_both_succeed(self):
        results = self.race(self.check_in, lambda: services.set_maintenance(self.slot.pk, True))
        self.assertCountEqual(results, ['success', 'conflict'])
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'occupied' if results[0] == 'success' else 'maintenance')
        self.assertEqual(ParkingRecord.objects.count(), 1 if results[0] == 'success' else 0)

    def test_check_in_and_zone_deactivation_cannot_partially_commit(self):
        other = ParkingSlot.objects.create(zone=self.zone, slot_number='A-02')
        results = self.race(self.check_in, lambda: services.update_zone(self.zone.pk, {'is_active': False}))
        self.assertCountEqual(results, ['success', 'conflict'])
        self.zone.refresh_from_db()
        self.slot.refresh_from_db()
        other.refresh_from_db()
        if results[0] == 'success':
            self.assertTrue(self.zone.is_active)
            self.assertTrue(self.slot.is_active)
            self.assertTrue(other.is_active)
            self.assertEqual(ParkingRecord.objects.count(), 1)
        else:
            self.assertFalse(self.zone.is_active)
            self.assertFalse(self.slot.is_active)
            self.assertFalse(other.is_active)
            self.assertFalse(ParkingRecord.objects.exists())

