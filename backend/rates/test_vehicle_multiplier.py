from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import ParkingRate


class VehicleMultiplierAPITests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username='multiplier_admin',
            password='TestPassword123!',
            role='Admin',
        )
        self.client = APIClient()
        token = AccessToken.for_user(self.admin)
        token['token_version'] = self.admin.token_version
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.rate = ParkingRate.objects.create(
            vehicle_type='Compact', hourly_rate=Decimal('40.00'),
        )

    def test_multiplier_defaults_to_one(self):
        self.assertEqual(self.rate.vehicle_multiplier, Decimal('1.00'))

    def test_admin_can_configure_vehicle_multiplier(self):
        response = self.client.patch(
            f'/api/v1/rates/{self.rate.pk}/',
            {'vehicle_multiplier': '1.50'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rate.refresh_from_db()
        self.assertEqual(self.rate.vehicle_multiplier, Decimal('1.50'))
        self.assertEqual(response.data['vehicle_multiplier'], '1.50')

    def test_negative_vehicle_multiplier_is_rejected(self):
        response = self.client.patch(
            f'/api/v1/rates/{self.rate.pk}/',
            {'vehicle_multiplier': '-0.50'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.rate.refresh_from_db()
        self.assertEqual(self.rate.vehicle_multiplier, Decimal('1.00'))
