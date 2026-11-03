"""US-25 aggregation, refresh, estimation and access regressions."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from billing.services import generate_receipt, record_payment
from operations.models import ParkingRecord
from operations.services import check_in_vehicle, check_out_vehicle
from parking_slots.models import ParkingSlot, ParkingZone
from rates.models import ParkingRate
from vehicles.models import Vehicle
from .dashboard import dashboard_metrics
from .serializers import REPORT_TIMEZONE


NOW = datetime(2026, 11, 3, 12, tzinfo=REPORT_TIMEZONE)
MIDNIGHT = NOW.replace(hour=0)


class DashboardTests(TestCase):
    url = '/api/reports/dashboard/'

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='dashboard_admin', role='Admin')
        cls.zone = ParkingZone.objects.create(name='A')
        cls.slot = ParkingSlot.objects.create(zone=cls.zone, slot_number='A1')
        cls.vehicle = Vehicle.objects.create(
            owner=cls.admin, registration_number='KA01AB1234', vehicle_type='Compact',
        )
        ParkingRate.objects.create(vehicle_type='Compact', hourly_rate='40.00')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.clock = patch('reports.dashboard.timezone.now', return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def record(self, entered=None, exited=None, slot=None, vehicle=None):
        return ParkingRecord.objects.create(
            vehicle=vehicle or self.vehicle, slot=slot or self.slot,
            check_in_time=entered or NOW - timedelta(hours=2), check_out_time=exited,
            status=ParkingRecord.Status.COMPLETED if exited else ParkingRecord.Status.ACTIVE,
            fee_amount=Decimal('10.10'), hourly_rate_snapshot=Decimal('10.10'), grace_period_minutes_snapshot=0,
        )

    def receipt(self, amount='10.10', paid_at=None, status='Paid'):
        record = self.record(exited=NOW - timedelta(hours=1))
        record.fee_amount = Decimal(amount)
        record.save(update_fields=['fee_amount'])
        receipt, _ = generate_receipt(record)
        if status != 'Pending':
            with patch('billing.services.timezone.now', return_value=paid_at or NOW - timedelta(minutes=1)):
                receipt, _ = record_payment(
                    receipt.receipt_number, self.admin, status,
                    payment_method='Cash' if status == 'Paid' else None,
                    payment_amount=Decimal(amount) if status == 'Paid' else Decimal('0.00'),
                )
        return receipt

    def metrics(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response.headers['Cache-Control'])
        return response.json()

    def test_empty_inventory_returns_zeroes_without_division_errors(self):
        self.slot.delete()
        data = self.metrics()
        self.assertEqual(data['total_slots'], 0)
        self.assertEqual(data['free_slots'], 0)
        self.assertEqual(data['occupancy_percent'], 0)
        self.assertEqual(data['zones'], [])
        self.assertEqual(data['today_revenue'], '0.00')
        self.assertIsNone(data['average_stay_minutes'])
        self.assertEqual(data['estimates']['next_hour_occupied_slots'], 0)
        self.assertEqual(len(data['activity']), 24)
        self.assertTrue(all(row['revenue'] == '0.00' for row in data['activity']))

    def test_distribution_excludes_inactive_inventory_and_reconciles(self):
        for state in ParkingSlot.Status.values:
            ParkingSlot.objects.create(zone=self.zone, slot_number=state, status=state)
        ParkingSlot.objects.create(zone=self.zone, slot_number='disabled', is_active=False)
        inactive = ParkingZone.objects.create(name='Inactive', is_active=False)
        ParkingSlot.objects.create(zone=inactive, slot_number='hidden')
        data = self.metrics()
        self.assertEqual(data['slot_distribution'], {'available': 2, 'occupied': 1, 'reserved': 1, 'maintenance': 1})
        self.assertEqual(data['total_slots'], 5)
        self.assertEqual(data['free_slots'], 2)
        self.assertEqual(data['occupancy_percent'], 20)
        self.assertEqual(sum(zone['total_slots'] for zone in data['zones']), 5)

    def test_active_record_overrides_stale_flags_without_double_counting(self):
        record = self.record()
        for state in ParkingSlot.Status.values:
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=state)
            with self.subTest(state=state):
                data = self.metrics()
                self.assertEqual(data['slot_distribution']['occupied'], 1)
                self.assertEqual(data['total_slots'], 1)
                self.assertEqual(data['free_slots'], 0)
        self.slot.is_active = False
        self.slot.save()
        data = self.metrics()
        self.assertEqual(data['active_sessions'], 1)  # Retain visibility of all open sessions.
        self.assertEqual(data['total_slots'], 0)
        self.assertEqual(data['estimates']['next_hour_occupied_slots'], 0)
        self.assertEqual(ParkingRecord.objects.get(pk=record.pk).status, 'ACTIVE')

    def test_refresh_reflects_real_checkin_checkout_and_payment(self):
        self.assertEqual(self.metrics()['active_sessions'], 0)
        with patch('operations.services.timezone.now', return_value=NOW - timedelta(hours=2)):
            record = check_in_vehicle(self.vehicle.registration_number, self.admin, slot_id=self.slot.pk)
        ParkingRecord.objects.filter(pk=record.pk).update(check_in_time=NOW - timedelta(hours=2))
        data = self.metrics()
        self.assertEqual((data['active_sessions'], data['free_slots']), (1, 0))
        self.assertEqual(data['arrivals_today'], 1)
        record = check_out_vehicle(self.vehicle.registration_number, self.admin)
        receipt, _ = generate_receipt(record)
        with patch('billing.services.timezone.now', return_value=NOW - timedelta(microseconds=1)):
            record_payment(receipt.receipt_number, self.admin, 'Paid', 'Cash', receipt.fee_amount)
        data = self.metrics()
        self.assertEqual((data['active_sessions'], data['free_slots']), (0, 1))
        self.assertEqual(data['today_revenue'], format(receipt.fee_amount, '.2f'))
        # The captured instant is exclusive; the next refresh sees this checkout.
        with patch('reports.dashboard.timezone.now', return_value=NOW + timedelta(seconds=1)):
            data = self.metrics()
        self.assertEqual(data['departures_today'], 1)
        self.assertEqual(data['average_stay_minutes'], 120)

    def test_revenue_uses_local_midnight_and_payment_time_not_checkout(self):
        self.receipt('1.10', paid_at=MIDNIGHT)
        self.receipt('2.20', paid_at=NOW - timedelta(microseconds=1))
        self.receipt('4.40', paid_at=MIDNIGHT - timedelta(microseconds=1))
        self.receipt('8.80', paid_at=NOW)
        self.receipt('16.00', status='Pending')
        self.receipt('32.00', status='Waived')
        data = self.metrics()
        self.assertEqual(data['today_revenue'], '3.30')
        self.assertEqual(data['activity'][0]['revenue'], '1.10')
        self.assertEqual(data['activity'][11]['revenue'], '2.20')
        self.assertEqual(data['revenue_start'], MIDNIGHT.isoformat())
        self.assertEqual(data['timezone'], 'Asia/Kolkata')
        self.assertEqual(data['estimates']['end_of_day_revenue'], '6.60')
        self.assertEqual(sum(Decimal(row['revenue']) for row in data['activity']), Decimal(data['today_revenue']))

    def test_large_receipt_totals_preserve_cents(self):
        self.receipt('999999999999.99')
        self.receipt('0.02')
        self.assertEqual(self.metrics()['today_revenue'], '1000000000000.01')

    def test_activity_boundaries_and_average_completed_stay(self):
        self.record(entered=MIDNIGHT, exited=NOW - timedelta(hours=1))
        self.record(entered=MIDNIGHT - timedelta(hours=1), exited=MIDNIGHT)
        self.record(entered=NOW, exited=NOW + timedelta(hours=1))
        data = self.metrics()
        self.assertEqual((data['arrivals_today'], data['departures_today']), (1, 2))
        self.assertEqual(data['activity'][0]['arrivals'], 1)
        self.assertEqual(data['activity'][0]['departures'], 1)
        self.assertEqual(data['activity'][11]['departures'], 1)
        self.assertEqual(data['average_stay_minutes'], 360)

    def test_revenue_estimate_waits_for_first_hour_and_handles_midnight(self):
        for instant in (MIDNIGHT, MIDNIGHT + timedelta(minutes=59)):
            with patch('reports.dashboard.timezone.now', return_value=instant):
                data = self.metrics()
                self.assertIsNone(data['estimates']['end_of_day_revenue'])
                self.assertEqual(data['today_revenue'], '0.00')
        with patch('reports.dashboard.timezone.now', return_value=MIDNIGHT + timedelta(hours=1)):
            self.assertEqual(self.metrics()['estimates']['end_of_day_revenue'], '0.00')

    def test_zero_duration_stay_is_reported_and_invalid_duration_is_excluded(self):
        self.record(entered=MIDNIGHT, exited=MIDNIGHT)
        self.record(entered=NOW, exited=NOW - timedelta(minutes=1))
        self.assertEqual(self.metrics()['average_stay_minutes'], 0)

    def test_next_hour_estimate_uses_recent_flow_and_capacity_bounds(self):
        self.record(entered=NOW - timedelta(minutes=30))
        # Recent arrivals cannot push predicted occupation above capacity.
        data = self.metrics()
        self.assertEqual(data['estimates']['recent_arrivals'], 1)
        self.assertEqual(data['estimates']['next_hour_occupied_slots'], 1)
        ParkingRecord.objects.all().delete()
        self.record(entered=NOW - timedelta(hours=2), exited=NOW - timedelta(minutes=1))
        data = self.metrics()
        self.assertEqual(data['estimates']['recent_departures'], 1)
        self.assertEqual(data['estimates']['next_hour_occupied_slots'], 0)

    def test_three_slots_and_recent_net_arrivals_predict_two_occupied(self):
        for number in ('A2', 'A3'):
            ParkingSlot.objects.create(zone=self.zone, slot_number=number)
        self.record(entered=NOW - timedelta(minutes=10))
        self.assertEqual(self.metrics()['estimates']['next_hour_occupied_slots'], 2)

    def test_access_is_admin_only_with_shared_errors(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
        for role in ('Operator', 'Customer'):
            self.client.force_authenticate(User.objects.create_user(username=role, role=role))
            response = self.client.get(self.url, {'role': 'Admin'})
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()['code'], 'PERMISSION_DENIED')

    def test_disabled_admins_are_denied(self):
        for field, value in (('status', 'suspended'), ('status', 'deactivated'), ('is_active', False)):
            self.admin.status, self.admin.is_active = 'active', True
            setattr(self.admin, field, value)
            self.admin.save()
            self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_bearer_auth_read_only_privacy_and_fixed_query_count(self):
        self.record()
        token = AccessToken.for_user(self.admin)
        token['token_version'] = self.admin.token_version
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        before = list(ParkingRecord.objects.values())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(ParkingRecord.objects.values()), before)
        for field in ('registration_number', 'ticket_qr_token', 'username', 'receipt_number'):
            self.assertNotIn(field, response.content.decode())
        with self.assertNumQueries(7):
            dashboard_metrics()
        for method in ('post', 'put', 'patch', 'delete'):
            self.assertEqual(getattr(self.client, method)(self.url, {}, format='json').status_code, 405)
