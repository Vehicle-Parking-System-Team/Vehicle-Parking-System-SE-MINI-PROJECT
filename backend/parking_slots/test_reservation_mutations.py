from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot, ParkingZone
from parking_slots import services
from reservations.models import Reservation
from vehicles.models import Vehicle
from vehicles.serializers import VehicleSerializer


class ConfirmedBookingMutationTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username='issue4_owner', role='Customer',
        )
        self.zone = ParkingZone.objects.create(name='Issue 4 zone')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='I4-1', vehicle_type='Compact',
        )
        self.vehicle = Vehicle.objects.create(
            owner=self.owner, registration_number='KA01I40001', vehicle_type='Compact',
        )
        self.reservation = Reservation.objects.create(
            customer=self.owner, vehicle=self.vehicle, slot=self.slot,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
        )

    def test_future_booking_blocks_slot_mutations_and_maintenance(self):
        for values in ({'is_active': False}, {'vehicle_type': 'SUV'}, {'floor': 2}):
            with self.subTest(values=values), self.assertRaises(Conflict):
                services.update_slot(self.slot.pk, values)
        with self.assertRaises(Conflict):
            services.set_maintenance(self.slot.pk, True)
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_active)
        self.assertEqual(self.slot.status, ParkingSlot.Status.AVAILABLE)

    def test_future_booking_blocks_zone_deactivation_but_not_rename(self):
        with self.assertRaises(Conflict):
            services.update_zone(self.zone.pk, {'is_active': False})
        services.update_zone(self.zone.pk, {'name': 'Renamed issue 4 zone'})
        self.zone.refresh_from_db()
        self.assertTrue(self.zone.is_active)
        self.assertEqual(self.zone.name, 'Renamed issue 4 zone')

    def test_future_booking_blocks_incompatible_vehicle_type_change(self):
        serializer = VehicleSerializer(
            self.vehicle, data={'vehicle_type': 'SUV'}, partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(Conflict):
            serializer.save()
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.vehicle_type, 'Compact')

    def test_compatible_vehicle_change_allowed_when_slot_accepts_any(self):
        self.slot.vehicle_type = 'any'
        self.slot.save(update_fields=['vehicle_type'])
        serializer = VehicleSerializer(
            self.vehicle, data={'vehicle_type': 'SUV'}, partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.vehicle_type, 'SUV')

    def test_cancelled_fulfilled_and_expired_bookings_do_not_block(self):
        for status in (Reservation.Status.CANCELLED, Reservation.Status.FULFILLED):
            with self.subTest(status=status):
                self.reservation.status = status
                self.reservation.save(update_fields=['status'])
                services.set_maintenance(self.slot.pk, True)
                services.set_maintenance(self.slot.pk, False)
        self.reservation.status = Reservation.Status.CONFIRMED
        self.reservation.start_time = timezone.now() - timedelta(days=2)
        self.reservation.end_time = timezone.now() - timedelta(days=1)
        self.reservation.save(update_fields=['status', 'start_time', 'end_time'])
        services.update_zone(self.zone.pk, {'is_active': False})
        self.zone.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertFalse(self.zone.is_active)
        self.assertFalse(self.slot.is_active)
        services.update_zone(self.zone.pk, {'is_active': True})
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_active)

    def test_api_returns_conflict_without_mutating_zone(self):
        client = APIClient()
        admin = get_user_model().objects.create_user(
            username='issue4_admin', role='Admin',
        )
        client.force_authenticate(user=admin)
        response = client.patch(
            f'/api/parking/zones/{self.zone.pk}/',
            {'is_active': False}, format='json',
        )
        self.assertEqual(response.status_code, 409, response.data)
        self.zone.refresh_from_db()
        self.assertTrue(self.zone.is_active)
