from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from common.exceptions import Conflict
from operations.services import check_in_vehicle
from rates.models import ParkingRate
from reservations.models import Reservation
from .models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle


class ReservationAvailabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.customer = users.create_user(username='private-customer', role='Customer')
        cls.operator = users.create_user(username='allocation-operator', role='Operator')
        cls.vehicle = Vehicle.objects.create(owner=cls.customer, registration_number='KA01AB1001', vehicle_type='Compact')
        cls.walk_in = Vehicle.objects.create(owner=cls.customer, registration_number='KA01AB1002', vehicle_type='Compact')
        cls.zone = ParkingZone.objects.create(name='Reservation zone')
        cls.slot = ParkingSlot.objects.create(zone=cls.zone, slot_number='R1', vehicle_type='Compact', floor=0)
        ParkingRate.objects.create(vehicle_type='Compact', hourly_rate='20.00')

    def setUp(self):
        self.client = APIClient()
        self.now = timezone.now()

    def reserve(self, **changes):
        values = dict(customer=self.customer, vehicle=self.vehicle, slot=self.slot,
                      start_time=self.now + timedelta(days=1), end_time=self.now + timedelta(days=1, hours=1))
        values.update(changes)
        return Reservation.objects.create(**values)

    def public_slot(self):
        response = self.client.get('/api/parking/availability/')
        self.assertEqual(response.status_code, 200)
        return response.data[0]

    def test_future_and_current_reservations_match_walk_in_rejection(self):
        reservation = self.reserve()
        for start in (self.now + timedelta(days=1), self.now - timedelta(minutes=5)):
            Reservation.objects.filter(pk=reservation.pk).update(start_time=start)
            row = self.public_slot()
            self.assertEqual(row['status'], 'reserved')
            self.assertTrue(row['reservation_protected'])
            self.assertFalse(row['walk_in_available'])
            with self.assertRaises(Conflict):
                check_in_vehicle(self.walk_in.registration_number, self.operator, self.slot.pk)
            self.slot.refresh_from_db()
            self.assertEqual(self.slot.status, 'available')  # projection never writes occupancy

    def test_expired_cancelled_and_fulfilled_windows_do_not_block(self):
        for status, end in [('Cancelled', self.now + timedelta(days=2)),
                            ('Fulfilled', self.now + timedelta(days=2)),
                            ('Confirmed', self.now - timedelta(seconds=1))]:
            with self.subTest(status=status):
                reservation = self.reserve(status=status, start_time=self.now - timedelta(days=1), end_time=end)
                row = self.public_slot()
                self.assertEqual(row['status'], 'available')
                self.assertFalse(row['reservation_protected'])
                self.assertTrue(row['walk_in_available'])
                reservation.delete()

    @override_settings(RESERVATION_BUFFER_MINUTES=10)
    def test_buffer_and_exact_expiry_boundary(self):
        reservation = self.reserve(start_time=self.now - timedelta(hours=1), end_time=self.now - timedelta(minutes=10))
        with patch('reservations.queries.timezone.now', return_value=self.now):
            self.assertTrue(self.public_slot()['walk_in_available'])
            Reservation.objects.filter(pk=reservation.pk).update(end_time=self.now - timedelta(minutes=9))
            self.assertFalse(self.public_slot()['walk_in_available'])
            with self.assertRaises(Conflict):
                check_in_vehicle(self.walk_in.registration_number, self.operator, self.slot.pk)

    def test_physical_states_take_precedence_and_management_retains_raw_status(self):
        self.reserve()
        self.client.force_authenticate(self.operator)
        response = self.client.get('/api/parking/slots/')
        self.assertEqual(response.data[0]['status'], 'available')
        self.assertTrue(response.data[0]['reservation_protected'])
        self.assertFalse(response.data[0]['walk_in_available'])
        for status in ('occupied', 'maintenance', 'reserved'):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=status)
            self.assertEqual(self.public_slot()['status'], status)
            self.assertFalse(self.public_slot()['walk_in_available'])

    def test_projection_is_private_and_uses_one_query_for_many_slots_and_bookings(self):
        self.reserve()
        for index in range(12):
            slot = ParkingSlot.objects.create(zone=self.zone, slot_number=f'Extra-{index}', vehicle_type='Compact')
            self.reserve(slot=slot)
        with self.assertNumQueries(1):
            response = self.client.get('/api/parking/availability/')
        self.assertTrue(all(row['reservation_protected'] for row in response.data))
        for secret in (self.customer.username, self.vehicle.registration_number, 'customer', 'vehicle_id', 'start_time', 'end_time'):
            self.assertNotIn(secret, response.content.decode())

    def test_booking_owner_can_still_arrive_without_reservation_code(self):
        self.reserve()
        record = check_in_vehicle(self.vehicle.registration_number, self.operator, self.slot.pk)
        self.assertEqual(record.slot_id, self.slot.pk)
        self.assertEqual(self.public_slot()['status'], 'occupied')
