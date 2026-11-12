from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from parking_slots.models import ParkingZone, ParkingSlot
from vehicles.models import Vehicle
from .models import Reservation


class ReservationReadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.owner = User.objects.create_user(username='reservation_read_owner', role='Customer')
        self.other = User.objects.create_user(username='reservation_read_other', role='Customer')
        self.operator = User.objects.create_user(username='reservation_read_operator', role='Operator')
        self.admin = User.objects.create_user(username='reservation_read_admin', role='Admin')
        zone = ParkingZone.objects.create(name='Reservation read zone')
        slot = ParkingSlot.objects.create(zone=zone, slot_number='READ-1', vehicle_type='Compact')
        vehicle = Vehicle.objects.create(owner=self.owner, registration_number='KA01RD1234', vehicle_type='Compact')
        self.reservation = Reservation.objects.create(
            customer=self.owner, vehicle=vehicle, slot=slot,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
        )

    def test_anonymous_read_is_rejected(self):
        self.assertEqual(self.client.get('/api/parking/reservations/').status_code, 401)
        self.assertEqual(self.client.get(f'/api/parking/reservations/{self.reservation.pk}/').status_code, 401)

    def test_customer_sees_only_own_reservations(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/parking/reservations/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.reservation.pk)
        self.assertEqual(self.client.get(f'/api/parking/reservations/{self.reservation.pk}/').status_code, 200)
        self.client.force_authenticate(user=self.other)
        self.assertEqual(self.client.get('/api/parking/reservations/').data['count'], 0)
        self.assertEqual(self.client.get(f'/api/parking/reservations/{self.reservation.pk}/').status_code, 404)

    def test_staff_can_inspect_and_filter(self):
        for user in (self.operator, self.admin):
            self.client.force_authenticate(user=user)
            response = self.client.get('/api/parking/reservations/?status=Confirmed')
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data['count'], 1)
            self.assertEqual(self.client.get(f'/api/parking/reservations/{self.reservation.pk}/').status_code, 200)

    def test_invalid_filter_and_pagination(self):
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.get('/api/parking/reservations/?status=Invalid').status_code, 400)
        self.assertEqual(self.client.get('/api/parking/reservations/?page=999').status_code, 404)
