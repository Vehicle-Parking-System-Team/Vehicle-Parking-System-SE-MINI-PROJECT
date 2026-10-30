"""US-15: overlap, buffer, cancellation and rescheduling regression coverage."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle
from .models import Reservation


@override_settings(RESERVATION_BUFFER_MINUTES=15)
class ReservationConflictBufferTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = get_user_model().objects.create_user(
            username='us15_customer', role='Customer',
        )
        self.client.force_authenticate(user=self.customer)
        self.vehicle = Vehicle.objects.create(
            registration_number='KA01US1501', vehicle_type='Compact',
            owner=self.customer,
        )
        self.second_vehicle = Vehicle.objects.create(
            registration_number='KA01US1502', vehicle_type='Compact',
            owner=self.customer,
        )
        zone = ParkingZone.objects.create(name='US15 Buffer Zone')
        self.slot = ParkingSlot.objects.create(
            zone=zone, slot_number='US15-A', vehicle_type='Compact',
        )
        self.other_slot = ParkingSlot.objects.create(
            zone=zone, slot_number='US15-B', vehicle_type='Compact',
        )
        self.start = timezone.now() + timedelta(days=3)
        self.existing = Reservation.objects.create(
            customer=self.customer, vehicle=self.vehicle, slot=self.slot,
            start_time=self.start, end_time=self.start + timedelta(hours=1),
        )

    def create(self, *, start, slot=None, vehicle=None):
        return self.client.post('/api/parking/reservations/', {
            'slot': (slot or self.slot).pk,
            'vehicle': (vehicle or self.second_vehicle).pk,
            'start_time': start.isoformat(),
            'duration_minutes': 30,
        }, format='json')

    def change(self, *, start):
        return self.client.patch(
            f'/api/parking/reservations/{self.existing.pk}/',
            {'start_time': start.isoformat(), 'duration_minutes': 30},
            format='json',
        )

    def test_slot_buffer_rejects_both_sides_and_exact_boundary_succeeds(self):
        for offset in (-44, 74):
            with self.subTest(offset=offset):
                response = self.create(start=self.start + timedelta(minutes=offset))
                self.assertEqual(response.status_code, 409, response.data)
        for offset in (-45, 75):
            with self.subTest(offset=offset):
                response = self.create(start=self.start + timedelta(minutes=offset))
                self.assertEqual(response.status_code, 201, response.data)
                Reservation.objects.exclude(pk=self.existing.pk).delete()

    def test_vehicle_buffer_applies_across_different_slots(self):
        response = self.create(
            start=self.start + timedelta(minutes=74),
            slot=self.other_slot, vehicle=self.vehicle,
        )
        self.assertEqual(response.status_code, 409, response.data)
        response = self.create(
            start=self.start + timedelta(minutes=75),
            slot=self.other_slot, vehicle=self.vehicle,
        )
        self.assertEqual(response.status_code, 201, response.data)

    def test_reschedule_checks_buffer_for_slot_and_vehicle(self):
        other = Reservation.objects.create(
            customer=self.customer, vehicle=self.vehicle,
            slot=self.other_slot,
            start_time=self.start + timedelta(hours=3),
            end_time=self.start + timedelta(hours=4),
        )
        response = self.change(start=other.start_time - timedelta(minutes=44))
        self.assertEqual(response.status_code, 409, response.data)
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.start_time, self.start)

        other.slot = self.slot
        other.vehicle = self.second_vehicle
        other.save(update_fields=['slot', 'vehicle'])
        response = self.change(start=other.start_time - timedelta(minutes=44))
        self.assertEqual(response.status_code, 409, response.data)
        response = self.change(start=other.start_time - timedelta(minutes=45))
        self.assertEqual(response.status_code, 200, response.data)

    def test_cancelled_reservations_do_not_hold_buffered_window(self):
        self.existing.status = Reservation.Status.CANCELLED
        self.existing.save(update_fields=['status'])
        response = self.create(start=self.start + timedelta(minutes=10))
        self.assertEqual(response.status_code, 201, response.data)

    def test_unrelated_vehicle_and_slot_can_share_time(self):
        response = self.create(start=self.start, slot=self.other_slot)
        self.assertEqual(response.status_code, 201, response.data)


@override_settings(RESERVATION_BUFFER_MINUTES=0)
class ZeroReservationBufferTests(TestCase):
    def test_back_to_back_booking_is_allowed_by_default(self):
        customer = get_user_model().objects.create_user(
            username='us15_zero_buffer', role='Customer',
        )
        vehicle = Vehicle.objects.create(
            registration_number='KA01US1599', vehicle_type='Compact',
            owner=customer,
        )
        zone = ParkingZone.objects.create(name='US15 Zero Buffer')
        slot = ParkingSlot.objects.create(
            zone=zone, slot_number='US15-Z', vehicle_type='Compact',
        )
        start = timezone.now() + timedelta(days=2)
        Reservation.objects.create(
            customer=customer, vehicle=vehicle, slot=slot,
            start_time=start, end_time=start + timedelta(hours=1),
        )
        client = APIClient()
        client.force_authenticate(user=customer)
        response = client.post('/api/parking/reservations/', {
            'slot': slot.pk, 'vehicle': vehicle.pk,
            'start_time': (start + timedelta(hours=1)).isoformat(),
            'duration_minutes': 30,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
