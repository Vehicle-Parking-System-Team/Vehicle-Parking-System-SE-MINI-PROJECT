from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from operations.services import check_in_vehicle
from vehicles.models import Vehicle
from .models import ParkingSlot, ParkingZone


URL = '/api/parking/availability/'


class AvailabilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.zone = ParkingZone.objects.create(name='Zone A')
        self.other_zone = ParkingZone.objects.create(name='Zone B')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='A-01', floor=0, vehicle_type='Compact',
        )
        self.other_slot = ParkingSlot.objects.create(
            zone=self.other_zone, slot_number='B-01', floor=-1,
            vehicle_type='SUV', status=ParkingSlot.Status.MAINTENANCE,
        )

    def test_anonymous_read_and_safe_fields(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(set(response.data[0]), {
            'id', 'zone', 'zone_name', 'zone_is_active', 'slot_number',
            'floor', 'status', 'vehicle_type', 'is_active',
        })

    def test_all_roles_can_read(self):
        for role in ('Admin', 'Operator', 'Customer'):
            user = get_user_model().objects.create_user(username=role, role=role)
            self.client.force_authenticate(user=user)
            self.assertEqual(self.client.get(URL).status_code, 200)

    def test_public_read_does_not_depend_on_credentials(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer expired-or-invalid')
        self.assertEqual(self.client.get(URL).status_code, 200)

    def test_read_only_even_for_admin(self):
        admin = get_user_model().objects.create_user(username='admin', role='Admin')
        for user in (None, admin):
            self.client.force_authenticate(user=user)
            for method in ('post', 'put', 'patch', 'delete'):
                with self.subTest(user=user, method=method):
                    response = getattr(self.client, method)(URL, {}, format='json')
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(set(response.data), {'error', 'code', 'details'})
        self.assertEqual(ParkingSlot.objects.count(), 2)

    def test_inactive_slots_and_zones_excluded(self):
        ParkingSlot.objects.filter(pk=self.slot.pk).update(is_active=False)
        ParkingZone.objects.filter(pk=self.other_zone.pk).update(is_active=False)
        self.assertEqual(self.client.get(URL).data, [])

    def test_all_active_states_remain_visible(self):
        for status in ParkingSlot.Status.values:
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=status)
            rows = self.client.get(URL, {'zone': self.zone.pk}).data
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['status'], status)

    def test_zone_filter(self):
        rows = self.client.get(URL, {'zone': self.other_zone.pk}).data
        self.assertEqual([row['id'] for row in rows], [self.other_slot.pk])

    def test_exact_vehicle_types(self):
        ParkingSlot.objects.create(zone=self.zone, slot_number='Legacy', vehicle_type='any')
        for vehicle_type, _ in Vehicle.VEHICLE_TYPE_CHOICES:
            ParkingSlot.objects.filter(pk=self.slot.pk).update(vehicle_type=vehicle_type)
            rows = self.client.get(URL, {'vehicle_type': vehicle_type}).data
            self.assertTrue(rows)
            self.assertTrue(all(row['vehicle_type'] == vehicle_type for row in rows))

    def test_combined_filters(self):
        rows = self.client.get(URL, {
            'zone': self.zone.pk, 'vehicle_type': 'SUV',
        }).data
        self.assertEqual(rows, [])

    def test_invalid_filters_use_shared_error_contract(self):
        for filters in ({'zone': 'bad'}, {'zone': '1.5'}, {'zone': 0}, {'vehicle_type': 'EV'}, {'vehicle_type': 'any'}):
            with self.subTest(filters=filters):
                response = self.client.get(URL, filters)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data['code'], 'VALIDATION_ERROR')
                self.assertEqual(set(response.data), {'error', 'code', 'details'})

    def test_unknown_zone_and_empty_facility_return_empty_array(self):
        self.assertEqual(self.client.get(URL, {'zone': 999999}).data, [])
        ParkingSlot.objects.all().delete()
        self.assertEqual(self.client.get(URL).data, [])

    def test_unmapped_floor_preserved(self):
        ParkingSlot.objects.filter(pk=self.slot.pk).update(floor=None)
        self.assertIsNone(self.client.get(URL, {'zone': self.zone.pk}).data[0]['floor'])

    def test_check_in_refreshes_occupancy_without_exposing_vehicle(self):
        operator = get_user_model().objects.create_user(username='operator', role='Operator')
        vehicle = Vehicle.objects.create(
            registration_number='KA01AB1234', vehicle_type='Compact', owner=operator,
            owner_name='Private Owner', owner_phone='1234567890',
        )
        self.assertEqual(self.client.get(URL).data[0]['status'], 'available')
        record = check_in_vehicle(vehicle.registration_number, operator, self.slot.pk)
        response = self.client.get(URL)
        self.assertEqual(response.data[0]['status'], 'occupied')
        payload = response.content.decode()
        for private in (vehicle.registration_number, vehicle.owner_name, vehicle.owner_phone, record.ticket_qr_token):
            self.assertNotIn(private, payload)

    def test_response_and_validation_errors_disable_caching(self):
        for params in ({}, {'zone': 'invalid'}):
            response = self.client.get(URL, params)
            self.assertIn('no-store', response['Cache-Control'])
            self.assertIn('no-cache', response['Cache-Control'])

    def test_serialization_has_no_per_slot_queries(self):
        for index in range(10):
            ParkingSlot.objects.create(zone=self.zone, slot_number=f'Extra-{index}')
        with self.assertNumQueries(1):
            response = self.client.get(URL)
            self.assertEqual(len(response.data), 12)

    def test_public_access_does_not_open_management_routes(self):
        customer = get_user_model().objects.create_user(username='customer', role='Customer')
        for user, expected in ((None, 401), (customer, 403)):
            self.client.force_authenticate(user=user)
            for method, url, data in (
                ('get', '/api/parking/slots/', {}),
                ('get', '/api/parking/zones/', {}),
                ('post', '/api/parking/slots/', {}),
                ('patch', f'/api/parking/slots/{self.slot.pk}/', {'is_active': False}),
                ('delete', f'/api/parking/slots/{self.slot.pk}/', {}),
                ('patch', f'/api/parking/slots/{self.slot.pk}/status/', {'status': 'maintenance'}),
            ):
                with self.subTest(user=user, method=method, url=url):
                    self.assertEqual(getattr(self.client, method)(url, data, format='json').status_code, expected)
