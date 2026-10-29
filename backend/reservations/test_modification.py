from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle
from .models import Reservation


class ReservationModificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.customer = User.objects.create_user(username='us14_owner', role='Customer')
        self.other = User.objects.create_user(username='us14_other', role='Customer')
        self.operator = User.objects.create_user(username='us14_operator', role='Operator')
        self.admin = User.objects.create_user(username='us14_admin', role='Admin')
        self.vehicle = Vehicle.objects.create(
            registration_number='KA01US1401', vehicle_type='Compact',
            owner=self.customer,
        )
        self.zone = ParkingZone.objects.create(name='US14 Zone')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='US14-1', vehicle_type='Compact',
        )
        self.start = timezone.now() + timedelta(days=2)
        self.reservation = Reservation.objects.create(
            customer=self.customer, vehicle=self.vehicle, slot=self.slot,
            start_time=self.start, end_time=self.start + timedelta(hours=1),
        )
        self.url = f'/api/parking/reservations/{self.reservation.pk}/'
        self.client.force_authenticate(user=self.customer)

    def test_owner_cancels_and_slot_can_be_rebooked(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.CANCELLED)
        response = self.client.post('/api/parking/reservations/', {
            'slot': self.slot.pk, 'vehicle': self.vehicle.pk,
            'start_time': self.start.isoformat(), 'duration_minutes': 60,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Reservation.objects.filter(
            slot=self.slot, status=Reservation.Status.CONFIRMED,
        ).count(), 1)

    def test_operator_and_admin_can_cancel(self):
        for role in ('operator', 'admin'):
            with self.subTest(role=role):
                self.client.force_authenticate(user=getattr(self, role))
                response = self.client.delete(self.url)
                self.assertEqual(response.status_code, 200, response.data)
                self.reservation.refresh_from_db()
                self.assertEqual(self.reservation.status, Reservation.Status.CANCELLED)
                self.reservation.status = Reservation.Status.CONFIRMED
                self.reservation.save(update_fields=['status'])

    def test_unrelated_customer_cannot_cancel_or_modify(self):
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.delete(self.url).status_code, 404)
        self.assertEqual(self.client.patch(self.url, {
            'start_time': (self.start + timedelta(hours=2)).isoformat(),
            'duration_minutes': 30,
        }, format='json').status_code, 404)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.CONFIRMED)

    def test_started_reservation_cannot_be_cancelled_or_modified(self):
        self.reservation.start_time = timezone.now() - timedelta(minutes=30)
        self.reservation.end_time = timezone.now() + timedelta(minutes=30)
        self.reservation.save(update_fields=['start_time', 'end_time'])
        self.assertEqual(self.client.delete(self.url).status_code, 400)
        self.assertEqual(self.client.patch(self.url, {
            'start_time': (timezone.now() + timedelta(days=3)).isoformat(),
            'duration_minutes': 60,
        }, format='json').status_code, 400)

    def test_future_reservation_can_be_cancelled_while_slot_is_occupied(self):
        # A different vehicle is currently parked in the slot. That does not
        # imply that this reservation (scheduled two days later) has started.
        self.slot.status = ParkingSlot.Status.OCCUPIED
        self.slot.save(update_fields=['status'])
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.CANCELLED)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, ParkingSlot.Status.OCCUPIED)

    def test_future_reservation_can_be_rescheduled_while_slot_is_occupied(self):
        self.slot.status = ParkingSlot.Status.OCCUPIED
        self.slot.save(update_fields=['status'])
        new_start = self.start + timedelta(hours=2)
        response = self.client.patch(self.url, {
            'start_time': new_start.isoformat(),
            'duration_minutes': 45,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.start_time, new_start)
        self.assertEqual(self.reservation.end_time, new_start + timedelta(minutes=45))
        self.assertEqual(self.reservation.status, Reservation.Status.CONFIRMED)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, ParkingSlot.Status.OCCUPIED)

    def test_started_reservation_on_occupied_slot_still_rejects_cancellation(self):
        self.reservation.start_time = timezone.now() - timedelta(minutes=10)
        self.reservation.end_time = timezone.now() + timedelta(minutes=50)
        self.reservation.save(update_fields=['start_time', 'end_time'])
        self.slot.status = ParkingSlot.Status.OCCUPIED
        self.slot.save(update_fields=['status'])
        self.assertEqual(self.client.delete(self.url).status_code, 400)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.CONFIRMED)

    def test_cancelled_reservation_cannot_be_cancelled_twice(self):
        self.assertEqual(self.client.delete(self.url).status_code, 200)
        self.assertEqual(self.client.delete(self.url).status_code, 400)

    def test_reschedule_and_reuse_old_window(self):
        new_start = self.start + timedelta(hours=2)
        response = self.client.patch(self.url, {
            'start_time': new_start.isoformat(), 'duration_minutes': 30,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.start_time, new_start)
        self.assertEqual(self.reservation.end_time, new_start + timedelta(minutes=30))
        response = self.client.post('/api/parking/reservations/', {
            'slot': self.slot.pk, 'vehicle': self.vehicle.pk,
            'start_time': self.start.isoformat(), 'duration_minutes': 60,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)

    def test_overlapping_reschedule_returns_409_without_changes(self):
        Reservation.objects.create(
            customer=self.customer, vehicle=self.vehicle, slot=self.slot,
            start_time=self.start + timedelta(hours=3),
            end_time=self.start + timedelta(hours=4),
        )
        response = self.client.patch(self.url, {
            'start_time': (self.start + timedelta(hours=3, minutes=30)).isoformat(),
            'duration_minutes': 30,
        }, format='json')
        self.assertEqual(response.status_code, 409, response.data)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.start_time, self.start)

    def test_reschedule_rejects_same_vehicle_booking_on_different_slot(self):
        other_slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='US14-2', vehicle_type='Compact',
        )
        conflicting_start = self.start + timedelta(hours=3)
        Reservation.objects.create(
            customer=self.customer, vehicle=self.vehicle, slot=other_slot,
            start_time=conflicting_start,
            end_time=conflicting_start + timedelta(hours=1),
        )
        response = self.client.patch(self.url, {
            'start_time': (conflicting_start + timedelta(minutes=15)).isoformat(),
            'duration_minutes': 30,
        }, format='json')
        self.assertEqual(response.status_code, 409, response.data)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.start_time, self.start)
        self.assertEqual(self.reservation.status, Reservation.Status.CONFIRMED)

    def test_reschedule_allows_adjacent_same_vehicle_booking(self):
        other_slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='US14-3', vehicle_type='Compact',
        )
        other_start = self.start + timedelta(hours=3)
        Reservation.objects.create(
            customer=self.customer, vehicle=self.vehicle, slot=other_slot,
            start_time=other_start, end_time=other_start + timedelta(hours=1),
        )
        response = self.client.patch(self.url, {
            'start_time': (other_start - timedelta(hours=1)).isoformat(),
            'duration_minutes': 60,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)

    def test_invalid_reschedule_returns_400(self):
        for data in (
            {'start_time': (timezone.now() - timedelta(days=1)).isoformat(), 'duration_minutes': 60},
            {'start_time': self.start.isoformat(), 'duration_minutes': 0},
            {'start_time': 'invalid', 'duration_minutes': 60},
        ):
            with self.subTest(data=data):
                self.assertEqual(self.client.patch(self.url, data, format='json').status_code, 400)

    def test_unauthenticated_request_denied(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.delete(self.url).status_code, 401)
