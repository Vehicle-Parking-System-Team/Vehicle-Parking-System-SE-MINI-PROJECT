from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from parking_slots.models import ParkingSlot, ParkingZone
from rates.calculations import calculate_parking_fee
from rates.models import ParkingRate
from vehicles.models import Vehicle

from .models import ParkingRecord
from .services import check_in_vehicle


CHECKOUT_URL = '/api/parking/check-out/'


class US22FeeAcceptanceTests(SimpleTestCase):
    """Focused tests for the three acceptance criteria in issue #42."""

    def test_session_within_grace_period_is_free(self):
        for duration in (timedelta(), timedelta(minutes=15)):
            with self.subTest(duration=duration):
                self.assertEqual(
                    calculate_parking_fee(
                        duration, Decimal('40.00'), 15, Decimal('1.50'),
                    ),
                    Decimal('0.00'),
                )

    def test_exceeded_grace_uses_rounded_hours_and_vehicle_multiplier(self):
        self.assertEqual(
            calculate_parking_fee(
                timedelta(minutes=61), Decimal('40.00'), 15, Decimal('1.50'),
            ),
            Decimal('120.00'),
        )

    def test_exact_hour_and_multi_day_rounding_is_deterministic(self):
        cases = (
            (timedelta(hours=1), '40.00'),
            (timedelta(hours=1, microseconds=1), '80.00'),
            (timedelta(days=2), '1920.00'),
            (timedelta(days=2, microseconds=1), '1960.00'),
        )
        for duration, expected in cases:
            with self.subTest(duration=duration):
                self.assertEqual(
                    calculate_parking_fee(duration, Decimal('40.00'), 15),
                    Decimal(expected),
                )

    def test_fractional_multiplier_rounds_currency_half_up(self):
        self.assertEqual(
            calculate_parking_fee(
                timedelta(hours=1), Decimal('12.35'), 15, Decimal('1.25'),
            ),
            Decimal('15.44'),
        )


class US22CheckoutMultiplierIntegrationTests(TestCase):
    def setUp(self):
        self.operator = get_user_model().objects.create_user(
            username='us22_operator', role='Operator',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)
        self.zone = ParkingZone.objects.create(name='US22 Zone')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='US22-01', floor=0, vehicle_type='Compact',
        )
        self.vehicle = Vehicle.objects.create(
            registration_number='KA22AB4242',
            vehicle_type='Compact',
            owner=self.operator,
        )
        self.rate = ParkingRate.objects.create(
            vehicle_type='Compact',
            hourly_rate=Decimal('40.00'),
            grace_period_minutes=15,
            vehicle_multiplier=Decimal('1.50'),
        )
        self.record = check_in_vehicle(
            self.vehicle.registration_number, self.operator, self.slot.pk,
        )
        self.exit_time = self.record.check_in_time + timedelta(minutes=61)

    def test_checkout_applies_and_snapshots_the_configured_multiplier(self):
        with patch('operations.services.timezone.now', return_value=self.exit_time):
            response = self.client.post(
                CHECKOUT_URL,
                {'registration_number': self.vehicle.registration_number},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['billable_hours'], 2)
        self.assertEqual(response.data['fee_amount'], '120.00')
        self.assertEqual(response.data['vehicle_multiplier_snapshot'], '1.50')

        ParkingRate.objects.filter(pk=self.rate.pk).update(
            vehicle_multiplier=Decimal('2.00'),
        )
        self.record.refresh_from_db()
        self.assertEqual(self.record.fee_amount, Decimal('120.00'))
        self.assertEqual(self.record.vehicle_multiplier_snapshot, Decimal('1.50'))
        self.assertEqual(ParkingRecord.objects.filter(status='COMPLETED').count(), 1)
