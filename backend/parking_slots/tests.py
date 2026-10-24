from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import ParkingSlot, ParkingZone


class ParkingSlotAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='parking_test_user',
            password='test-password-123',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.zone = ParkingZone.objects.create(name='Test Zone')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number='A-01',
        )

    def test_list_zones(self):
        response = self.client.get('/api/parking/zones/')
        self.assertEqual(response.status_code, 200)

    def test_create_zone(self):
        response = self.client.post(
            '/api/parking/zones/',
            {'name': 'North Zone', 'description': 'Test area'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            ParkingZone.objects.filter(name='North Zone').exists()
        )

    def test_list_slots(self):
        response = self.client.get('/api/parking/slots/')
        self.assertEqual(response.status_code, 200)

    def test_filter_slots_by_zone(self):
        response = self.client.get(
            f'/api/parking/slots/?zone={self.zone.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_update_slot_status(self):
        response = self.client.patch(
            f'/api/parking/slots/{self.slot.id}/status/',
            {'status': 'occupied'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, 'occupied')

    def test_reject_invalid_slot_status(self):
        response = self.client.patch(
            f'/api/parking/slots/{self.slot.id}/status/',
            {'status': 'invalid'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
