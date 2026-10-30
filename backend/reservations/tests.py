from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle
from .models import Reservation


class ReservationCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='customer13', password='example-test-password', role='Customer',
        )
        self.other = get_user_model().objects.create_user(
            username='other13', role='Customer',
        )
        self.vehicle = Vehicle.objects.create(
            registration_number='KA01AB1313', vehicle_type='Compact', owner=self.user,
        )
        self.other_vehicle = Vehicle.objects.create(
            registration_number='KA01AB1314', vehicle_type='Compact', owner=self.other,
        )
        zone = ParkingZone.objects.create(name='Reservation Zone')
        self.slot = ParkingSlot.objects.create(
            zone=zone, slot_number='R-1', floor=0, vehicle_type='Compact',
        )
        self.second_slot = ParkingSlot.objects.create(
            zone=zone, slot_number='R-2', floor=0, vehicle_type='SUV',
        )
        self.client.force_authenticate(user=self.user)
        self.start = timezone.now() + timedelta(days=2)

    def payload(self, **changes):
        data = {
            'slot': self.slot.pk,
            'vehicle': self.vehicle.pk,
            'start_time': self.start.isoformat(),
            'duration_minutes': 60,
        }
        data.update(changes)
        return data

    def test_confirmed_creation_returns_201(self):
        response = self.client.post('/api/parking/reservations/', self.payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], 'Confirmed')
        self.assertEqual(Reservation.objects.count(), 1)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.customer_id, self.user.pk)
        self.assertEqual(reservation.end_time, reservation.start_time + timedelta(hours=1))

    def test_overlapping_window_returns_409(self):
        self.client.post('/api/parking/reservations/', self.payload(), format='json')
        for start in (self.start, self.start + timedelta(minutes=30)):
            with self.subTest(start=start):
                response = self.client.post(
                    '/api/parking/reservations/',
                    self.payload(start_time=start.isoformat()), format='json',
                )
                self.assertEqual(response.status_code, 409)
                self.assertEqual(response.data['code'], 'CONFLICT')
        self.assertEqual(Reservation.objects.count(), 1)

    def test_adjacent_windows_are_allowed(self):
        self.assertEqual(self.client.post(
            '/api/parking/reservations/', self.payload(), format='json',
        ).status_code, 201)
        response = self.client.post('/api/parking/reservations/', self.payload(
            start_time=(self.start + timedelta(hours=1)).isoformat(),
        ), format='json')
        self.assertEqual(response.status_code, 201)

    def test_invalid_times_and_duration_return_400(self):
        for changes in (
            {'start_time': (timezone.now() - timedelta(days=1)).isoformat()},
            {'start_time': 'invalid'},
            {'duration_minutes': 0},
            {'duration_minutes': -1},
            {'duration_minutes': 'invalid'},
        ):
            with self.subTest(changes=changes):
                response = self.client.post(
                    '/api/parking/reservations/', self.payload(**changes), format='json',
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data['code'], 'VALIDATION_ERROR')
                self.assertTrue(response.data['details'])
        self.assertEqual(Reservation.objects.count(), 0)

    def test_vehicle_ownership_and_compatibility(self):
        for changes in (
            {'vehicle': self.other_vehicle.pk},
            {'slot': self.second_slot.pk},
        ):
            response = self.client.post(
                '/api/parking/reservations/', self.payload(**changes), format='json',
            )
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_inactive_and_maintenance_slot(self):
        self.slot.status = ParkingSlot.Status.MAINTENANCE
        self.slot.save()
        self.assertEqual(self.client.post(
            '/api/parking/reservations/', self.payload(), format='json',
        ).status_code, 409)
        self.slot.status = ParkingSlot.Status.AVAILABLE
        self.slot.is_active = False
        self.slot.save()
        self.assertEqual(self.client.post(
            '/api/parking/reservations/', self.payload(), format='json',
        ).status_code, 400)

    def test_anonymous_cannot_reserve(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(
            '/api/parking/reservations/', self.payload(), format='json',
        ).status_code, 401)

    def test_admin_cannot_create_reservations(self):
        for role in ('Admin',):
            with self.subTest(role=role):
                staff = get_user_model().objects.create_user(
                    username='staff_' + role.lower(), role=role,
                )
                self.client.force_authenticate(user=staff)
                response = self.client.post(
                    '/api/parking/reservations/', self.payload(), format='json',
                )
                self.assertEqual(response.status_code, 403, response.data)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_customer_cannot_reserve_other_customers_vehicle(self):
        response = self.client.post(
            '/api/parking/reservations/',
            self.payload(vehicle=self.other_vehicle.pk), format='json',
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_inactive_zone_returns_400_without_creating_reservation(self):
        self.slot.zone.is_active = False
        self.slot.zone.save(update_fields=['is_active'])
        response = self.client.post(
            '/api/parking/reservations/', self.payload(), format='json',
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_occupied_slot_returns_409_without_creating_reservation(self):
        self.slot.status = ParkingSlot.Status.OCCUPIED
        self.slot.save(update_fields=['status'])
        response = self.client.post(
            '/api/parking/reservations/', self.payload(), format='json',
        )
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_operator_reserves_for_vehicle_owner(self):
        operator = get_user_model().objects.create_user(
            username='reservation_operator_13', role='Operator',
        )
        self.client.force_authenticate(user=operator)
        response = self.client.post(
            '/api/parking/reservations/',
            self.payload(vehicle=self.other_vehicle.pk), format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.customer_id, self.other.pk)
        self.assertEqual(reservation.vehicle_id, self.other_vehicle.pk)
        self.assertNotEqual(reservation.customer_id, operator.pk)

    def test_operator_cannot_override_reservation_customer(self):
        operator = get_user_model().objects.create_user(
            username='reservation_operator_override_13', role='Operator',
        )
        self.client.force_authenticate(user=operator)
        response = self.client.post(
            '/api/parking/reservations/',
            self.payload(vehicle=self.other_vehicle.pk, customer=self.user.pk),
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Reservation.objects.get().customer_id, self.other.pk)
        self.assertEqual(response.data['customer'], self.other.pk)

    def test_operator_cannot_reserve_vehicle_for_noncustomer_owner(self):
        operator = get_user_model().objects.create_user(
            username='reservation_operator_invalid_13', role='Operator',
        )
        staff_vehicle = Vehicle.objects.create(
            registration_number='KA01OP1313', vehicle_type='Compact', owner=operator,
        )
        self.client.force_authenticate(user=operator)
        response = self.client.post(
            '/api/parking/reservations/',
            self.payload(vehicle=staff_vehicle.pk), format='json',
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(Reservation.objects.count(), 0)
