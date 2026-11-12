from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from parking_slots.models import ParkingSlot, ParkingZone
from reservations.services import create_reservation
from vehicles.models import Vehicle


class LockedVehicleBookingTests(TestCase):
    def test_stale_vehicle_instance_cannot_confirm_incompatible_booking(self):
        customer = get_user_model().objects.create_user(
            username='issue4_stale_vehicle', role='Customer',
        )
        vehicle = Vehicle.objects.create(
            owner=customer, registration_number='KA01AB4444',
            vehicle_type='Compact',
        )
        slot = ParkingSlot.objects.create(
            zone=ParkingZone.objects.create(name='Issue 4 stale vehicle zone'),
            slot_number='STALE-1', vehicle_type='Compact',
        )
        stale_vehicle = Vehicle.objects.get(pk=vehicle.pk)
        Vehicle.objects.filter(pk=vehicle.pk).update(vehicle_type='SUV')
        start = timezone.now() + timedelta(days=2)
        with self.assertRaises(ValidationError):
            create_reservation(
                actor=customer, customer=customer, vehicle=stale_vehicle,
                slot=slot, start_time=start, end_time=start + timedelta(hours=1),
            )
        self.assertFalse(slot.reservations.exists())
