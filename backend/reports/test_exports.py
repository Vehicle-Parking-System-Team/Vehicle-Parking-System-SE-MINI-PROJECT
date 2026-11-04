import csv
import io
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from operations.models import ParkingRecord
from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle
from .exports import safe_cell


class ExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='export-admin', role='Admin')
        cls.zone = ParkingZone.objects.create(name='=HYPERLINK("bad")')
        cls.slot = ParkingSlot.objects.create(zone=cls.zone, slot_number='A,1')
        cls.vehicle = Vehicle.objects.create(owner=cls.admin, registration_number='KA01AB1234', vehicle_type='Compact')
        cls.now = timezone.now().replace(microsecond=0)
        cls.record = ParkingRecord.objects.create(
            vehicle=cls.vehicle, slot=cls.slot, check_in_time=cls.now,
            registration_number_snapshot='OLD123', slot_number_snapshot='Old,1',
            vehicle_type_at_checkin_snapshot='Compact',
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.query = {'start': self.now.isoformat(), 'end': (self.now + timedelta(days=1)).isoformat()}

    def export(self, **params):
        return self.client.get('/api/reports/export/', {**self.query, **params})

    def csv_rows(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        return list(csv.reader(io.StringIO(b''.join(response.streaming_content).decode('utf-8-sig'))))

    def test_csv_headers_snapshots_quoting_and_formula_protection(self):
        response = self.export()
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        rows = self.csv_rows(response)
        self.assertEqual(rows[1][1:4], ['OLD123', 'Old,1', "'=HYPERLINK(\"bad\")"])
        self.assertEqual(rows[1][-2:], ['', 'Pending'])
        for value in ('=1', '+1', '-1', '@SUM(A1)', '  =1', '\t1', '\r1', '\n1'):
            self.assertTrue(safe_cell(value).startswith("'"))

    def test_filters_and_half_open_time_range(self):
        self.assertEqual(len(self.csv_rows(self.export(zone=self.zone.pk, vehicle_type='Compact'))), 2)
        for params in ({'status': 'COMPLETED'}, {'vehicle_type': 'SUV'},
                       {'end': self.now.isoformat(), 'start': (self.now - timedelta(days=1)).isoformat()}):
            self.assertEqual(len(self.csv_rows(self.export(**params))), 1)

    def test_empty_csv_still_has_columns(self):
        rows = self.csv_rows(self.export(status='COMPLETED'))
        self.assertEqual(rows[0][0], 'id')
        self.assertEqual(len(rows), 1)

    def test_vehicle_filter_prefers_snapshot_and_supports_legacy_rows(self):
        Vehicle.objects.filter(pk=self.vehicle.pk).update(vehicle_type='SUV')
        self.assertEqual(len(self.csv_rows(self.export(vehicle_type='Compact'))), 2)
        self.assertEqual(len(self.csv_rows(self.export(vehicle_type='SUV'))), 1)
        ParkingRecord.objects.filter(pk=self.record.pk).update(vehicle_type_at_checkin_snapshot=None)
        self.assertEqual(len(self.csv_rows(self.export(vehicle_type='SUV'))), 2)

    def test_invalid_queries_fail_before_streaming(self):
        for params in ({'export_format': 'exe'}, {'report': 'unknown'}, {'status': 'bad'},
                       {'end': self.now.isoformat()}, {'zone': 9999}, {'report': 'revenue', 'zone': 1},
                       {'end': (self.now + timedelta(days=367)).isoformat()}):
            response = self.export(**params)
            self.assertIn(response.status_code, (400, 404))
            self.assertIn('code', response.json())

    def test_aggregate_csv_matches_existing_reports(self):
        with patch('reports.services.timezone.now', return_value=self.now):
            for report in ('occupancy', 'revenue'):
                rows = self.csv_rows(self.export(report=report))
                data = self.client.get(f'/api/reports/{report}/', self.query).json()['results']
                self.assertEqual(rows[0], list(data[0]))
                self.assertEqual(rows[1:], [[safe_cell(value) for value in row.values()] for row in data])

    def test_pdf_is_valid_and_empty_data_is_supported(self):
        for report in ('logs', 'occupancy', 'revenue'):
            response = self.export(report=report, export_format='pdf')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            body = b''.join(response.streaming_content)
            self.assertTrue(body.startswith(b'%PDF-'))
            self.assertIn(b'%%EOF', body)

    def test_pdf_limit_is_error_not_truncation(self):
        with patch('reports.exports.report_rows', return_value=(('id',), ((i,) for i in range(10001)))):
            response = self.export(export_format='pdf')
        self.assertEqual(response.status_code, 400)

    def test_csv_rows_are_lazy_and_query_count_is_constant(self):
        with self.assertNumQueries(0):
            response = self.export()
            stream = iter(response.streaming_content)
            next(stream)  # Header does not read the dataset.
        with self.assertNumQueries(1):
            list(stream)
        ParkingRecord.objects.filter(pk=self.record.pk).update(status='COMPLETED')
        ParkingRecord.objects.bulk_create([
            ParkingRecord(vehicle=self.vehicle, slot=self.slot, check_in_time=self.now, status='COMPLETED')
            for _ in range(2000)
        ])
        with self.assertNumQueries(1):
            self.assertEqual(len(self.csv_rows(self.export())), 2002)

    def test_only_admin_can_download(self):
        for role in ('Operator', 'Customer'):
            user = User.objects.create_user(username=role, role=role)
            self.client.force_authenticate(user)
            for file_format in ('csv', 'pdf'):
                self.assertEqual(self.export(export_format=file_format).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.export().status_code, 401)
