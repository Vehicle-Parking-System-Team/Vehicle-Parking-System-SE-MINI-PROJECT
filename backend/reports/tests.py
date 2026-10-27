"""US-26 API, aggregation, boundary and authorization regressions."""

from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from operations.models import ParkingRecord
from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle
from .serializers import REPORT_TIMEZONE


def local_time(day=20, hour=0, minute=0):
    return datetime(2026, 10, day, hour, minute, tzinfo=REPORT_TIMEZONE)


class OccupancyReportTests(TestCase):
    url = '/api/reports/occupancy/'

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='report_admin', role='Admin')
        cls.zone = ParkingZone.objects.create(name='North')
        cls.other_zone = ParkingZone.objects.create(name='South')
        cls.slot = ParkingSlot.objects.create(zone=cls.zone, slot_number='N1')
        cls.second_slot = ParkingSlot.objects.create(zone=cls.zone, slot_number='N2')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        clock = patch('reports.services.timezone.now', return_value=local_time(22, 12))
        clock.start()
        self.addCleanup(clock.stop)

    def report(self, **params):
        query = {'start': '2026-10-20T10:00:00+05:30', 'end': '2026-10-20T12:00:00+05:30',
                 'interval': 'hour', 'zone': self.zone.pk}
        query.update(params)
        return self.client.get(self.url, query)

    def record(self, start, end=None, slot=None):
        vehicle = Vehicle.objects.create(
            owner=self.admin, registration_number=f'KA-01-AB-{Vehicle.objects.count() + 1:04d}',
            vehicle_type='Compact',
        )
        return ParkingRecord.objects.create(
            vehicle=vehicle, slot=slot or self.slot,
            check_in_time=start, check_out_time=end,
            status=ParkingRecord.Status.ACTIVE if end is None else ParkingRecord.Status.COMPLETED,
        )

    def test_hourly_utilization_uses_slot_time_and_exposes_baseline(self):
        self.record(local_time(hour=10, minute=15), local_time(hour=11, minute=30))
        response = self.report()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['timezone'], 'Asia/Kolkata')
        self.assertEqual(data['capacity_basis'], 'current_total_slot_inventory')
        self.assertEqual(data['zone_basis'], 'current_slot_zone')
        self.assertEqual([row['occupied_slot_minutes'] for row in data['results']], [45, 30])
        self.assertEqual([row['utilization_percent'] for row in data['results']], [37.5, 25])
        self.assertEqual([row['entries'] for row in data['results']], [1, 0])
        self.assertEqual(data['peak_hours'][0]['hours'], [10])
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_daily_grouping_splits_midnight_and_preserves_totals(self):
        self.record(local_time(20, 23, 30), local_time(21, 0, 30))
        response = self.report(start='2026-10-20T23:00:00', end='2026-10-21T01:00:00', interval='day')
        self.assertEqual(response.status_code, 200)
        rows = response.json()['results']
        self.assertEqual(len(rows), 2)
        self.assertEqual([row['occupied_slot_minutes'] for row in rows], [30, 30])
        self.assertEqual([row['entries'] for row in rows], [1, 0])
        self.assertEqual(response.json()['peak_hours'][0]['hours'], [0, 23])

    def test_default_daily_report_reconciles_with_hourly_totals(self):
        self.record(local_time(hour=10, minute=15), local_time(hour=11, minute=30))
        hourly = self.report().json()['results']
        response = self.client.get(self.url, {
            'start': '2026-10-20T10:00:00', 'end': '2026-10-20T12:00:00', 'zone': self.zone.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['interval'], 'day')
        daily = response.json()['results'][0]
        self.assertEqual(daily['occupied_slot_minutes'], sum(row['occupied_slot_minutes'] for row in hourly))
        self.assertEqual(daily['entries'], sum(row['entries'] for row in hourly))
        self.assertEqual(daily['utilization_percent'], 31.25)

    def test_sessions_are_clipped_to_requested_range(self):
        self.record(local_time(hour=9), local_time(hour=13))
        rows = self.report().json()['results']
        self.assertEqual([row['occupied_slot_minutes'] for row in rows], [60, 60])
        self.assertEqual([row['entries'] for row in rows], [0, 0])

    def test_inclusive_start_and_exclusive_end(self):
        self.record(local_time(hour=9), local_time(hour=10))
        self.record(local_time(hour=10), local_time(hour=11))
        self.record(local_time(hour=12), local_time(hour=13))
        rows = self.report().json()['results']
        self.assertEqual([row['occupied_slot_minutes'] for row in rows], [60, 0])
        self.assertEqual([row['entries'] for row in rows], [1, 0])

    def test_partial_hours_use_actual_requested_duration(self):
        self.record(local_time(hour=10), local_time(hour=12))
        rows = self.report(start='2026-10-20T10:30:00', end='2026-10-20T11:15:00').json()['results']
        self.assertEqual([row['observed_minutes'] for row in rows], [30, 15])
        self.assertEqual([row['occupied_slot_minutes'] for row in rows], [30, 15])
        self.assertEqual([row['utilization_percent'] for row in rows], [50, 50])

    def test_active_and_completed_sessions_stop_at_captured_now(self):
        self.record(local_time(22, 10, 30))
        self.record(local_time(22, 11), local_time(22, 13), slot=self.second_slot)
        rows = self.report(start='2026-10-22T10:00:00', end='2026-10-22T14:00:00').json()['results']
        self.assertEqual([row['occupied_slot_minutes'] for row in rows], [30, 120, 0, 0])
        self.assertEqual([row['observed_minutes'] for row in rows], [60, 60, 0, 0])
        self.assertEqual([row['utilization_percent'] for row in rows], [25, 100, 0, 0])

    def test_zero_activity_and_zero_capacity_return_zero_rows(self):
        response = self.report(zone=self.other_zone.pk)
        self.assertEqual(response.status_code, 200)
        for row in response.json()['results']:
            self.assertEqual(row['slot_count'], 0)
            self.assertEqual(row['occupied_slot_minutes'], 0)
            self.assertEqual(row['utilization_percent'], 0)
            self.assertEqual(row['entries'], 0)
        self.assertEqual(response.json()['peak_hours'][0]['hours'], [])

    def test_future_range_has_zero_observed_time(self):
        rows = self.report(start='2026-10-23T10:00:00', end='2026-10-23T12:00:00').json()['results']
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row['observed_minutes'] == 0 for row in rows))

    def test_current_capacity_includes_inactive_and_maintenance_slots(self):
        self.second_slot.is_active = False
        self.second_slot.status = ParkingSlot.Status.MAINTENANCE
        self.second_slot.save()
        self.record(local_time(hour=10), local_time(hour=11))
        row = self.report().json()['results'][0]
        self.assertEqual(row['slot_count'], 2)
        self.assertEqual(row['utilization_percent'], 50)

    def test_zone_filter_and_current_zone_attribution(self):
        self.record(local_time(hour=10), local_time(hour=11))
        self.slot.zone = self.other_zone
        self.slot.save()
        self.assertEqual(self.report().json()['results'][0]['occupied_slot_minutes'], 0)
        other = self.report(zone=self.other_zone.pk).json()['results'][0]
        self.assertEqual(other['occupied_slot_minutes'], 60)
        self.assertEqual(other['utilization_percent'], 100)

    def test_all_zones_include_empty_zone_without_n_plus_one_queries(self):
        self.record(local_time(hour=10), local_time(hour=11))
        with self.assertNumQueries(2):
            response = self.client.get(self.url, {
                'start': '2026-10-20T10:00:00', 'end': '2026-10-20T12:00:00', 'interval': 'hour',
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 4)

    def test_utc_offsets_convert_to_local_time(self):
        response = self.report(start='2026-10-20T04:30:00Z', end='2026-10-20T06:30:00Z')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['start'], '2026-10-20T10:00:00+05:30')

    def test_peak_hours_accumulate_across_dates_and_include_ties(self):
        self.record(local_time(20, 10), local_time(20, 11))
        self.record(local_time(21, 10), local_time(21, 11))
        self.record(local_time(20, 11), local_time(20, 12), slot=self.second_slot)
        response = self.report(start='2026-10-20T00:00:00', end='2026-10-22T00:00:00', interval='day')
        self.assertEqual(response.json()['peak_hours'][0], {
            'zone_id': self.zone.pk, 'hours': [10], 'occupied_slot_minutes': 120,
        })

    def test_invalid_filters_return_shared_validation_errors(self):
        for params in (
            {'end': '2026-10-20T09:00:00'}, {'end': '2026-10-20T10:00:00'},
            {'start': 'invalid'}, {'interval': 'week'}, {'zone': 0}, {'zone': 'invalid'},
            {'end': '2028-01-01T00:00:00'},
        ):
            with self.subTest(params=params):
                response = self.report(**params)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()['code'], 'VALIDATION_ERROR')
                self.assertTrue(response.json()['details'])

    def test_required_date_filters(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()['details']), {'start', 'end'})

    def test_unknown_zone_returns_application_not_found(self):
        response = self.report(zone=999999)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['code'], 'NOT_FOUND')

    def test_result_limit_rejects_large_zone_period_products(self):
        response = self.client.get(self.url, {
            'start': '2026-01-01T00:00:00', 'end': '2027-01-01T00:00:00', 'interval': 'hour',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], 'VALIDATION_ERROR')

    def test_unauthenticated_and_non_admin_access_is_denied(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.report().status_code, 401)
        for role in ('Operator', 'Customer'):
            with self.subTest(role=role):
                user = User.objects.create_user(username=f'report_{role}', role=role)
                self.client.force_authenticate(user)
                response = self.report()
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()['code'], 'PERMISSION_DENIED')

    def test_inactive_admin_is_denied(self):
        for field, value in (('status', 'suspended'), ('status', 'deactivated'), ('is_active', False)):
            with self.subTest(field=field, value=value):
                self.admin.refresh_from_db()
                setattr(self.admin, field, value)
                self.admin.save()
                self.client.force_authenticate(self.admin)
                self.assertEqual(self.report().status_code, 403)
                self.admin.status = 'active'
                self.admin.is_active = True
                self.admin.save()

    def test_real_bearer_token_and_read_only_response(self):
        token = AccessToken.for_user(self.admin)
        token['token_version'] = self.admin.token_version
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        record = self.record(local_time(hour=10), local_time(hour=11))
        before = list(ParkingRecord.objects.values())
        response = self.report()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(ParkingRecord.objects.values()), before)
        body = response.json()
        self.assertNotIn('registration_number', str(body))
        self.assertNotIn('ticket_qr_token', str(body))
        self.assertEqual(record.status, ParkingRecord.Status.COMPLETED)

    def test_write_methods_are_not_exposed(self):
        self.assertEqual(self.client.post(self.url, {}).status_code, 405)
