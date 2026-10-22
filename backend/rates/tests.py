from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from rates.models import ParkingRate

User = get_user_model()


class ParkingRateAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = User.objects.create_user(
            username='rate_admin',
            password='TestPassword123!',
            role='Admin',
        )
        self.customer = User.objects.create_user(
            username='rate_customer',
            password='TestPassword123!',
            role='Customer',
        )

        self.rate = ParkingRate.objects.create(
            vehicle_type='Compact',
            hourly_rate='30.00',
            grace_period_minutes=10,
            penalty_fee='100.00',
        )

    def authenticate_as(self, user):
        token = AccessToken.for_user(user)
        token['token_version'] = user.token_version
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

    def test_admin_can_update_rate(self):
        self.authenticate_as(self.admin)

        response = self.client.patch(
            f'/api/v1/rates/{self.rate.pk}/',
            {'hourly_rate': '45.00'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rate.refresh_from_db()
        self.assertEqual(str(self.rate.hourly_rate), '45.00')

    def test_customer_cannot_update_rate(self):
        self.authenticate_as(self.customer)

        response = self.client.patch(
            f'/api/v1/rates/{self.rate.pk}/',
            {'hourly_rate': '45.00'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_negative_hourly_rate_is_rejected(self):
        self.authenticate_as(self.admin)

        response = self.client.patch(
            f'/api/v1/rates/{self.rate.pk}/',
            {'hourly_rate': '-5.00'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.rate.refresh_from_db()
        self.assertEqual(str(self.rate.hourly_rate), '30.00')

    def test_invalid_grace_period_is_rejected(self):
        self.authenticate_as(self.admin)

        response = self.client.patch(
            f'/api/v1/rates/{self.rate.pk}/',
            {'grace_period_minutes': -1},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_admin_can_list_rates(self):
        self.authenticate_as(self.admin)

        response = self.client.get('/api/v1/rates/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_default_grace_period_is_15_minutes(self):
        rate = ParkingRate.objects.create(
            vehicle_type='SUV',
            hourly_rate='50.00',
        )

        self.assertEqual(rate.grace_period_minutes, 15)

    def test_suspended_customer_cannot_read_rates(self):
        self.customer.status = 'suspended'
        self.customer.save(update_fields=['status'])
        self.authenticate_as(self.customer)

        response = self.client.get('/api/v1/rates/')

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

    def test_deactivated_customer_cannot_read_rates(self):
        self.customer.status = 'deactivated'
        self.customer.save(update_fields=['status'])
        self.authenticate_as(self.customer)

        response = self.client.get('/api/v1/rates/')

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

    def test_inactive_django_user_cannot_read_rates(self):
        self.customer.is_active = False
        self.customer.save(update_fields=['is_active'])
        self.authenticate_as(self.customer)

        response = self.client.get('/api/v1/rates/')

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ],
        )

        
    def test_suspended_customer_using_session_login_cannot_read_rates(self):
        self.customer.status = 'suspended'
        self.customer.save(update_fields=['status'])

        logged_in = self.client.login(
            username='rate_customer',
            password='TestPassword123!',
        )
        self.assertTrue(logged_in, 'Session login should succeed for this test.')

        response = self.client.get('/api/v1/rates/')

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

