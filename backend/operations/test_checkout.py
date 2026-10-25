from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import close_old_connections, connections
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.test import APIClient

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot, ParkingZone
from parking_slots.services import release_slot as real_release_slot
from rates.calculations import calculate_parking_fee
from rates.models import ParkingRate
from vehicles.models import Vehicle
from .checkout import check_out_vehicle
from .models import ParkingRecord
from .services import check_in_vehicle


URL = '/api/parking/check-out/'


class ParkingFeeTests(SimpleTestCase):
    def test_grace_hour_and_multi_day_boundaries(self):
        for duration, expected in (
            (timedelta(), '0.00'),
            (timedelta(minutes=15), '0.00'),
            (timedelta(minutes=15, microseconds=1), '40.00'),
            (timedelta(hours=1), '40.00'),
            (timedelta(hours=1, microseconds=1), '80.00'),
            (timedelta(minutes=61), '80.00'),
            (timedelta(days=2, microseconds=1), '1960.00'),
        ):
            with self.subTest(duration=duration):
                self.assertEqual(calculate_parking_fee(duration, Decimal('40.00'), 15), Decimal(expected))

    def test_configured_grace_and_decimal_tariff(self):
        self.assertEqual(calculate_parking_fee(timedelta(minutes=30), Decimal('12.35'), 30), Decimal('0.00'))
        self.assertEqual(calculate_parking_fee(timedelta(minutes=31), Decimal('12.35'), 30), Decimal('12.35'))
        self.assertEqual(calculate_parking_fee(timedelta(microseconds=1), Decimal('12.35'), 0), Decimal('12.35'))
        self.assertEqual(calculate_parking_fee(timedelta(hours=2), Decimal('0.00'), 0), Decimal('0.00'))

    def test_invalid_tariffs_and_grace_are_conflicts(self):
        for rate in (Decimal('-1'), Decimal('NaN'), Decimal('Infinity'), Decimal('0.001'), Decimal('100000000'), None, 40.0):
            with self.subTest(rate=rate), self.assertRaises(Conflict):
                calculate_parking_fee(timedelta(hours=1), rate, 15)
        for grace in (-1, None, True, 1.5):
            with self.subTest(grace=grace), self.assertRaises(Conflict):
                calculate_parking_fee(timedelta(hours=1), Decimal('40.00'), grace)

    def test_negative_duration_and_amount_overflow_are_conflicts(self):
        for duration, rate in (
            (timedelta(microseconds=-1), Decimal('40.00')),
            (timedelta(days=100000), Decimal('99999999.99')),
        ):
            with self.assertRaises(Conflict):
                calculate_parking_fee(duration, rate, 15)


class CheckoutAPITests(TestCase):
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
        self.rate = ParkingRate.objects.create(
            vehicle_type='Compact', hourly_rate=Decimal('40.00'), grace_period_minutes=15,
            penalty_fee=Decimal('500.00'),
        )
        self.record = check_in_vehicle(self.vehicle.registration_number, self.operator, self.slot.pk)
        self.exit_time = self.record.check_in_time + timedelta(minutes=61)

    def checkout(self, **extra):
        with patch('operations.checkout.timezone.now', return_value=self.exit_time):
            return self.client.post(URL, {'registration_number': self.vehicle.registration_number, **extra}, format='json')

    def assert_still_parked(self):
        self.record.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(self.record.status, 'ACTIVE')
        self.assertIsNone(self.record.check_out_time)
        self.assertIsNone(self.record.fee_amount)
        self.assertIsNone(self.record.hourly_rate_snapshot)
        self.assertIsNone(self.record.grace_period_minutes_snapshot)
        self.assertIsNone(self.record.vehicle_type_snapshot)
        self.assertEqual(self.slot.status, 'occupied')

    def test_real_check_in_fee_checkout_and_public_availability(self):
        before = self.client.get('/api/parking/availability/').data
        self.assertEqual(before[0]['status'], 'occupied')
        response = self.checkout()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'COMPLETED')
        self.assertEqual(response.data['duration_seconds'], '3660.000000')
        self.assertEqual(response.data['billable_hours'], 2)
        self.assertEqual(response.data['fee_amount'], '80.00')
        self.assertEqual(response.data['currency'], 'INR')
        self.assertEqual(response.data['hourly_rate_snapshot'], '40.00')
        self.assertEqual(response.data['grace_period_minutes_snapshot'], 15)
        self.assertEqual(response.data['vehicle_type_snapshot'], 'Compact')
        self.record.refresh_from_db()
        self.assertEqual(self.record.check_out_time, self.exit_time)
        self.assertEqual(self.record.fee_amount, Decimal('80.00'))
        self.assertEqual(self.record.operator_id, self.operator.pk)
        self.assertNotIn('payment_status', response.data)
        after = self.client.get('/api/parking/availability/').data
        self.assertEqual(after[0]['status'], 'available')
        self.assertNotIn('fee_amount', after[0])

    def test_free_checkout_still_completes_and_releases(self):
        self.exit_time = self.record.check_in_time + timedelta(minutes=15)
        response = self.checkout()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['fee_amount'], '0.00')
        self.assertEqual(response.data['billable_hours'], 0)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'available')

    def test_admin_can_checkout_without_replacing_check_in_operator(self):
        admin = get_user_model().objects.create_user(username='admin', role='Admin')
        self.client.force_authenticate(user=admin)
        self.assertEqual(self.checkout().status_code, 200)
        self.record.refresh_from_db()
        self.assertEqual(self.record.operator_id, self.operator.pk)

    def test_anonymous_and_customer_cannot_checkout(self):
        customer = get_user_model().objects.create_user(username='customer', role='Customer')
        for user, expected in ((None, 401), (customer, 403)):
            self.client.force_authenticate(user=user)
            response = self.checkout()
            self.assertEqual(response.status_code, expected)
            self.assertEqual(set(response.data), {'error', 'code', 'details'})
            self.assert_still_parked()

    def test_inactive_operator_and_direct_customer_service_are_denied(self):
        for status, active in (('suspended', True), ('deactivated', True), ('active', False)):
            self.operator.status, self.operator.is_active = status, active
            self.assertEqual(self.checkout().status_code, 403)
            self.assert_still_parked()
        customer = get_user_model().objects.create_user(username='customer', role='Customer')
        with self.assertRaises(PermissionDenied):
            check_out_vehicle(self.vehicle.registration_number, customer)

    def test_missing_blank_and_malformed_plate_are_rejected(self):
        for payload in ({}, {'registration_number': ''}, {'registration_number': ' '}, {'registration_number': 'X' * 21}):
            response = self.client.post(URL, payload, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data['code'], 'VALIDATION_ERROR')
            self.assert_still_parked()

    def test_client_cannot_supply_fee_time_status_or_payment(self):
        for field, value in (('fee_amount', '0.00'), ('check_out_time', '2020-01-01'), ('status', 'COMPLETED'), ('payment_status', 'PAID'), ('slot_id', self.slot.pk)):
            response = self.checkout(**{field: value})
            self.assertEqual(response.status_code, 400)
            self.assert_still_parked()

    def test_unknown_and_repeated_checkout_return_404(self):
        response = self.client.post(URL, {'registration_number': 'UNKNOWN'}, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.checkout().status_code, 200)
        self.assertEqual(self.checkout().status_code, 404)
        self.assertEqual(ParkingRecord.objects.count(), 1)

    def test_plate_normalization_and_reentry_after_checkout(self):
        with patch('operations.checkout.timezone.now', return_value=self.exit_time):
            response = self.client.post(URL, {'registration_number': '  ka01ab1234  '})
        self.assertEqual(response.status_code, 200)
        second = check_in_vehicle(self.vehicle.registration_number, self.operator, self.slot.pk)
        self.assertNotEqual(second.pk, self.record.pk)
        self.assertEqual(ParkingRecord.objects.filter(status='ACTIVE').count(), 1)

    def test_missing_or_invalid_tariff_keeps_record_and_slot_unchanged(self):
        self.rate.delete()
        response = self.checkout()
        self.assertEqual(response.status_code, 409)
        self.assert_still_parked()
        ParkingRate.objects.create(vehicle_type='Compact', hourly_rate=Decimal('-1.00'))
        self.assertEqual(self.checkout().status_code, 409)
        self.assert_still_parked()

    def test_future_check_in_does_not_close_record(self):
        self.exit_time = self.record.check_in_time - timedelta(microseconds=1)
        self.assertEqual(self.checkout().status_code, 409)
        self.assert_still_parked()

    def test_inconsistent_active_record_is_not_silently_rewritten(self):
        ParkingRecord.objects.filter(pk=self.record.pk).update(check_out_time=self.exit_time)
        self.assertEqual(self.checkout().status_code, 409)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'ACTIVE')
        self.assertIsNone(self.record.fee_amount)
        self.assertEqual(self.record.check_out_time, self.exit_time)

    def test_current_configured_rate_is_used_then_snapshot_is_preserved(self):
        ParkingRate.objects.filter(pk=self.rate.pk).update(hourly_rate=Decimal('12.35'), grace_period_minutes=30)
        self.assertEqual(self.checkout().data['fee_amount'], '24.70')
        ParkingRate.objects.filter(pk=self.rate.pk).update(hourly_rate=Decimal('99.00'))
        self.record.refresh_from_db()
        self.assertEqual(self.record.fee_amount, Decimal('24.70'))
        self.assertEqual(self.record.hourly_rate_snapshot, Decimal('12.35'))
        self.assertEqual(self.record.grace_period_minutes_snapshot, 30)

    def test_slot_release_failure_rolls_back_completed_record_and_fee(self):
        def fail_after_release(slot_id):
            real_release_slot(slot_id)
            raise Conflict('Simulated downstream release failure.')
        with patch('operations.checkout.release_slot', side_effect=fail_after_release):
            self.assertEqual(self.checkout().status_code, 409)
        self.assert_still_parked()

    def test_record_save_failure_does_not_release_bay(self):
        with patch.object(ParkingRecord, 'save', side_effect=RuntimeError('private failure')):
            response = self.checkout()
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('private failure', str(response.data))
        self.assert_still_parked()

    def test_inconsistent_slot_state_rolls_back_fee_and_completion(self):
        ParkingSlot.objects.filter(pk=self.slot.pk).update(status='maintenance')
        self.assertEqual(self.checkout().status_code, 409)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'ACTIVE')
        self.assertIsNone(self.record.fee_amount)
        self.assertIsNone(self.record.check_out_time)

    def test_check_in_response_is_unchanged(self):
        self.assertEqual(self.checkout().status_code, 200)
        response = self.client.post('/api/parking/check-in/', {
            'registration_number': self.vehicle.registration_number, 'slot_id': self.slot.pk,
        })
        self.assertEqual(response.status_code, 201)
        self.assertNotIn('fee_amount', response.data)
        self.assertNotIn('hourly_rate_snapshot', response.data)


@skipUnlessDBFeature('has_select_for_update')
class CheckoutConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(username='operator', role='Operator')
        self.zone = ParkingZone.objects.create(name='Zone A')
        self.slot = ParkingSlot.objects.create(zone=self.zone, slot_number='A-01', vehicle_type='Compact')
        self.vehicle = Vehicle.objects.create(
            registration_number='KA01AB1234', vehicle_type='Compact', owner=self.operator,
        )
        ParkingRate.objects.create(vehicle_type='Compact', hourly_rate=Decimal('40.00'))
        self.record = check_in_vehicle(self.vehicle.registration_number, self.operator, self.slot.pk)

    def race(self, *actions):
        barrier = Barrier(len(actions))
        def run(action):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return action()
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            futures = [pool.submit(run, action) for action in actions]
            return [future.result(timeout=30) for future in futures]

    def checkout(self):
        try:
            check_out_vehicle(self.vehicle.registration_number, self.operator)
            return 'completed'
        except NotFound:
            return 'not_found'

    def test_two_checkouts_have_one_completion_and_one_not_found(self):
        self.assertCountEqual(self.race(self.checkout, self.checkout), ['completed', 'not_found'])
        self.record.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(self.record.status, 'COMPLETED')
        self.assertIsNotNone(self.record.fee_amount)
        self.assertEqual(self.slot.status, 'available')

    def test_checkout_and_new_allocation_preserve_record_slot_consistency(self):
        other = Vehicle.objects.create(registration_number='KA01AB5678', vehicle_type='Compact', owner=self.operator)
        def allocate():
            try:
                check_in_vehicle(other.registration_number, self.operator, self.slot.pk)
                return 'allocated'
            except Conflict:
                return 'conflict'
        results = self.race(self.checkout, allocate)
        self.assertEqual(results[0], 'completed')
        self.assertIn(results[1], ('allocated', 'conflict'))
        self.record.refresh_from_db()
        self.slot.refresh_from_db()
        active = ParkingRecord.objects.filter(slot=self.slot, status='ACTIVE').count()
        self.assertEqual(self.record.status, 'COMPLETED')
        self.assertEqual(active, 1 if results[1] == 'allocated' else 0)
        self.assertEqual(self.slot.status, 'occupied' if active else 'available')


class CheckoutMigrationTests(TransactionTestCase):
    def test_existing_active_and_completed_records_survive_nullable_snapshot_migration(self):
        executor = MigrationExecutor(connection)
        restore = executor.loader.graph.leaf_nodes()
        before = [('operations', '0002_parkingrecord_delete_parkingsession_and_more')]
        after = [('operations', '0003_checkout_fee_snapshots')]
        executor.migrate(before)
        try:
            apps = executor.loader.project_state(before).apps
            User = apps.get_model('accounts', 'User')
            Zone = apps.get_model('parking_slots', 'ParkingZone')
            Slot = apps.get_model('parking_slots', 'ParkingSlot')
            Car = apps.get_model('vehicles', 'Vehicle')
            Record = apps.get_model('operations', 'ParkingRecord')
            owner = User.objects.create(username='legacy')
            zone = Zone.objects.create(name='Legacy')
            for index, status in enumerate(('ACTIVE', 'COMPLETED')):
                slot = Slot.objects.create(zone=zone, slot_number=f'Old-{index}', status='occupied' if index == 0 else 'available')
                vehicle = Car.objects.create(registration_number=f'LEGACY{index}', vehicle_type='Compact', owner=owner)
                stamp = timezone.now() - timedelta(days=1)
                Record.objects.create(vehicle=vehicle, slot=slot, operator=owner, status=status,
                                      check_in_time=stamp, check_out_time=None if index == 0 else stamp + timedelta(hours=1))
            rows = list(Record.objects.order_by('pk').values())
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            Record = executor.loader.project_state(after).apps.get_model('operations', 'ParkingRecord')
            self.assertEqual(list(Record.objects.order_by('pk').values(*rows[0].keys())), rows)
            for row in Record.objects.values():
                for field in ('fee_amount', 'hourly_rate_snapshot', 'grace_period_minutes_snapshot', 'vehicle_type_snapshot'):
                    self.assertIsNone(row[field])
        finally:
            MigrationExecutor(connection).migrate(restore)
