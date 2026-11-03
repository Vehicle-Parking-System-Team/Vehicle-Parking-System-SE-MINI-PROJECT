"""US-27 reconciliation, filter, date-boundary and access regressions."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from billing.models import BillingReceipt
from billing.services import generate_receipt, record_payment
from operations.models import ParkingRecord
from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle
from .serializers import REPORT_TIMEZONE


def local_time(day=2, hour=12, minute=0):
    return datetime(2026, 11, day, hour, minute, tzinfo=REPORT_TIMEZONE)


class RevenueReportTests(TestCase):
    url = '/api/reports/revenue/'

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='revenue_admin', role='Admin')
        cls.zone = ParkingZone.objects.create(name='Revenue zone')
        cls.slot = ParkingSlot.objects.create(zone=cls.zone, slot_number='R1')
        cls.vehicle = Vehicle.objects.create(
            owner=cls.admin, registration_number='KA01AB1234', vehicle_type='Compact',
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def report(self, **params):
        query = {'start': '2026-11-02T00:00:00', 'end': '2026-11-03T00:00:00'}
        query.update(params)
        return self.client.get(self.url, query)

    def receipt(self, amount='10.00', method='Cash', vehicle_type='Compact',
                paid_at=None, status='Paid'):
        record = ParkingRecord.objects.create(
            vehicle=self.vehicle, slot=self.slot,
            check_in_time=local_time(1, 10), check_out_time=local_time(1, 11),
            status=ParkingRecord.Status.COMPLETED, fee_amount=Decimal(amount),
            hourly_rate_snapshot=Decimal('10.00'), grace_period_minutes_snapshot=0,
            vehicle_type_at_checkin_snapshot=vehicle_type,
        )
        receipt, _ = generate_receipt(record)
        if status != 'Pending':
            with patch('billing.services.timezone.now', return_value=paid_at or local_time()):
                receipt, _ = record_payment(
                    receipt.receipt_number, self.admin, status,
                    payment_method=method if status == 'Paid' else None,
                    payment_amount=Decimal(amount) if status == 'Paid' else Decimal('0.00'),
                )
        return receipt

    def test_paid_receipts_and_breakdowns_reconcile_exactly(self):
        self.receipt('10.10', 'Cash', 'Compact')
        self.receipt('20.20', 'Card', 'SUV')
        self.receipt('30.30', 'UPI', 'Two-Wheeler')
        response = self.report()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['totals'], {'receipt_count': 3, 'revenue': '60.60'})
        for name in ('results', 'by_payment_method', 'by_vehicle_type'):
            self.assertEqual(sum(Decimal(row['revenue']) for row in data[name]), Decimal('60.60'))
            self.assertEqual(sum(row['receipt_count'] for row in data[name]), 3)
        self.assertEqual(data['date_basis'], 'payment_timestamp')
        self.assertEqual(data['revenue_basis'], 'collected_paid_receipts')
        self.assertEqual(data['vehicle_basis'], 'receipt_snapshot')
        self.assertEqual(data['currency'], 'INR')
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_pending_waived_and_active_sessions_do_not_contribute(self):
        self.receipt('20.00', status='Pending')
        self.receipt('30.00', status='Waived')
        paid = self.receipt('40.00')
        ParkingRecord.objects.filter(pk=paid.parking_record_id).update(status='ACTIVE')
        self.assertEqual(self.report().json()['totals'], {'receipt_count': 0, 'revenue': '0.00'})

    def test_payment_time_instead_of_checkout_or_receipt_creation_time(self):
        self.receipt('12.34')  # Checkout was on November 1; settlement on November 2.
        self.assertEqual(self.report().json()['totals']['revenue'], '12.34')
        self.assertEqual(self.report(start='2026-11-01', end='2026-11-02').json()['totals']['revenue'], '0.00')

    def test_start_is_inclusive_and_end_is_exclusive(self):
        self.receipt('1.00', paid_at=local_time(2, 0))
        self.receipt('2.00', paid_at=local_time(3, 0) - timedelta(microseconds=1))
        self.receipt('4.00', paid_at=local_time(3, 0))
        self.receipt('8.00', paid_at=local_time(2, 0) - timedelta(microseconds=1))
        self.assertEqual(self.report().json()['totals'], {'receipt_count': 2, 'revenue': '3.00'})

    def test_utc_offsets_and_naive_dates_use_kolkata(self):
        self.receipt(paid_at=local_time(2, 0))
        local = self.report().json()
        utc = self.report(start='2026-11-01T18:30:00Z', end='2026-11-02T18:30:00Z').json()
        self.assertEqual(utc, local)
        self.assertEqual(local['timezone'], 'Asia/Kolkata')
        self.assertEqual(local['start'], '2026-11-02T00:00:00+05:30')

    def test_daily_periods_split_at_local_midnight(self):
        self.receipt('1.10', paid_at=local_time(2, 23, 59))
        self.receipt('2.20', paid_at=local_time(3, 0))
        data = self.report(start='2026-11-02T23:30:00', end='2026-11-03T00:30:00').json()
        self.assertEqual([row['revenue'] for row in data['results']], ['1.10', '2.20'])
        self.assertEqual(data['results'][0]['end'], '2026-11-03T00:00:00+05:30')

    def test_hourly_partial_periods_and_zero_buckets(self):
        self.receipt('1.10', paid_at=local_time(2, 10, 15))
        self.receipt('2.20', paid_at=local_time(2, 11))
        self.receipt('4.40', paid_at=local_time(2, 11, 15))
        data = self.report(start='2026-11-02T09:30:00', end='2026-11-02T11:15:00', interval='hour').json()
        self.assertEqual([row['revenue'] for row in data['results']], ['0.00', '1.10', '2.20'])
        self.assertEqual(data['results'][0]['start'], '2026-11-02T09:30:00+05:30')
        self.assertEqual(data['results'][-1]['end'], '2026-11-02T11:15:00+05:30')

    def test_hourly_and_daily_totals_match(self):
        self.receipt('1.10', paid_at=local_time(2, 10))
        self.receipt('2.20', paid_at=local_time(2, 11))
        daily = self.report().json()
        hourly = self.report(interval='hour').json()
        self.assertEqual(hourly['totals'], daily['totals'])
        self.assertEqual(sum(Decimal(row['revenue']) for row in hourly['results']), Decimal('3.30'))

    def test_method_and_vehicle_filters_intersect(self):
        self.receipt('1.10', 'Cash', 'Compact')
        self.receipt('2.20', 'Card', 'Compact')
        self.receipt('4.40', 'Cash', 'SUV')
        self.assertEqual(self.report(payment_method='Cash').json()['totals']['revenue'], '5.50')
        self.assertEqual(self.report(vehicle_type='Compact').json()['totals']['revenue'], '3.30')
        data = self.report(payment_method='Cash', vehicle_type='Compact').json()
        self.assertEqual(data['totals']['revenue'], '1.10')
        self.assertEqual(data['filters'], {'payment_method': 'Cash', 'vehicle_type': 'Compact'})

    def test_vehicle_category_uses_receipt_snapshot(self):
        self.receipt('2.20', vehicle_type='SUV')
        Vehicle.objects.filter(pk=self.vehicle.pk).update(vehicle_type='Two-Wheeler')
        self.assertEqual(self.report(vehicle_type='SUV').json()['totals']['revenue'], '2.20')
        self.assertEqual(self.report(vehicle_type='Two-Wheeler').json()['totals']['revenue'], '0.00')

    def test_repeated_receipt_generation_and_settlement_count_once(self):
        receipt = self.receipt('12.34')
        again, created = generate_receipt(receipt.parking_record)
        self.assertFalse(created)
        self.assertEqual(again.pk, receipt.pk)
        _, changed = record_payment(receipt.receipt_number, self.admin, 'Paid', 'Cash', Decimal('12.34'))
        self.assertFalse(changed)
        self.assertEqual(self.report().json()['totals'], {'receipt_count': 1, 'revenue': '12.34'})

    def test_empty_and_unmatched_reports_return_zero_values(self):
        self.receipt()
        for params in ({'payment_method': 'UPI'}, {'start': '2027-01-01', 'end': '2027-01-03'}):
            with self.subTest(params=params):
                data = self.report(**params).json()
                self.assertEqual(data['totals'], {'receipt_count': 0, 'revenue': '0.00'})
                self.assertTrue(data['results'])
                self.assertTrue(all(row['revenue'] == '0.00' for row in data['results']))

    def test_other_currencies_are_not_added_to_inr(self):
        receipt = self.receipt('50.00')
        BillingReceipt.objects.filter(pk=receipt.pk).update(currency='USD')
        self.receipt('10.00')
        self.assertEqual(self.report().json()['totals']['revenue'], '10.00')

    def test_exact_cents_and_large_aggregate(self):
        self.receipt('999999999999.99')
        self.receipt('999999999999.99')
        self.receipt('0.01')
        self.assertEqual(self.report().json()['totals']['revenue'], '1999999999999.99')

    def test_zero_fee_paid_receipt_counts_without_adding_revenue(self):
        self.receipt('0.00')
        self.assertEqual(self.report().json()['totals'], {'receipt_count': 1, 'revenue': '0.00'})

    def test_invalid_filters_use_shared_error_contract(self):
        for params in (
            {'start': 'invalid'}, {'end': '2026-11-01'}, {'end': '2026-11-02'},
            {'end': '2028-01-01'}, {'interval': 'month'}, {'payment_method': 'cash'},
            {'vehicle_type': 'invalid'}, {'payment_method': "Cash' OR 1=1--"},
        ):
            with self.subTest(params=params):
                response = self.report(**params)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()['code'], 'VALIDATION_ERROR')
                self.assertTrue(response.json()['details'])

    def test_dates_are_required_and_366_day_limit_is_inclusive(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['details']), {'start', 'end'})
        response = self.report(start='2026-01-01', end='2027-01-02', interval='hour')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 366 * 24)

    def test_anonymous_and_non_admins_are_denied(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.report().status_code, 401)
        for role in ('Operator', 'Customer'):
            user = User.objects.create_user(username=f'revenue_{role}', role=role)
            self.client.force_authenticate(user)
            response = self.report(role='Admin')
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()['code'], 'PERMISSION_DENIED')

    def test_suspended_deactivated_and_inactive_admins_are_denied(self):
        for field, value in (('status', 'suspended'), ('status', 'deactivated'), ('is_active', False)):
            with self.subTest(field=field):
                self.admin.status, self.admin.is_active = 'active', True
                setattr(self.admin, field, value)
                self.admin.save()
                self.assertEqual(self.report().status_code, 403)

    def test_real_bearer_token_read_only_and_no_personal_data(self):
        self.receipt()
        token = AccessToken.for_user(self.admin)
        token['token_version'] = self.admin.token_version
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        before = list(BillingReceipt.objects.values())
        response = self.report()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(BillingReceipt.objects.values()), before)
        for field in ('registration_number', 'receipt_number', 'payment_recorded_by', 'ticket_qr_token'):
            self.assertNotIn(field, response.content.decode())

    def test_write_methods_are_not_exposed(self):
        for method in ('post', 'put', 'patch', 'delete'):
            self.assertEqual(getattr(self.client, method)(self.url, {}, format='json').status_code, 405)

    def test_report_uses_one_data_query(self):
        self.receipt('1.10', 'Cash')
        self.receipt('2.20', 'UPI')
        with self.assertNumQueries(1):
            response = self.report()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['totals']['revenue'], '3.30')
