"""
Automated unit and API tests for US-05: Vehicle Registration (FR-01, TC-UC02-UNIT-001, TC-UC02-API-001).
Tests model persistence, normalization, uniqueness constraints, ownership safeguards,
error envelopes conforming to US-31, and callable service interface for Member 3.
"""

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from common.exceptions import Conflict
from vehicles.models import Vehicle
from vehicles.services import (
    get_vehicle_by_plate,
    get_vehicle_by_registration_number,
    normalize_registration_number,
    register_vehicle,
)

User = get_user_model()


class VehicleModelAndServiceTests(TestCase):
    """Unit tests for Vehicle model, plate normalization, and service functions (TC-UC02-UNIT-001)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='vehicle_owner_1',
            email='owner1@parking.local',
            password='Password123!',
            role='Customer',
        )
        self.other_user = User.objects.create_user(
            username='vehicle_owner_2',
            email='owner2@parking.local',
            password='Password123!',
            role='Customer',
        )

    def test_normalize_registration_number_trims_and_uppercases(self):
        self.assertEqual(normalize_registration_number('  ka-01-ab-1234  '), 'KA-01-AB-1234')
        self.assertEqual(normalize_registration_number('dl3cbb1122'), 'DL3CBB1122')
        self.assertEqual(normalize_registration_number(''), '')
        self.assertEqual(normalize_registration_number(None), '')

    def test_create_vehicle_persists_and_normalizes_plate(self):
        vehicle = Vehicle.objects.create(
            registration_number='  mh-12-cd-5678 ',
            vehicle_type='Compact',
            owner=self.user,
            owner_name='Owner One',
            owner_phone='9998887776',
        )
        self.assertEqual(vehicle.registration_number, 'MH-12-CD-5678')
        self.assertEqual(vehicle.plate_number, 'MH-12-CD-5678')
        self.assertEqual(vehicle.vehicle_type, 'Compact')
        self.assertEqual(vehicle.owner, self.user)
        self.assertIsNotNone(vehicle.created_at)

    def test_database_enforces_plate_uniqueness(self):
        Vehicle.objects.create(
            registration_number='KA-01-MJ-9999',
            vehicle_type='SUV',
            owner=self.user,
        )
        with self.assertRaises(IntegrityError):
            Vehicle.objects.create(
                registration_number='KA-01-MJ-9999',
                vehicle_type='Compact',
                owner=self.other_user,
            )

    def test_service_get_vehicle_by_registration_number_found_and_not_found(self):
        Vehicle.objects.create(
            registration_number='DL-05-XY-0001',
            vehicle_type='Two-Wheeler',
            owner=self.user,
        )

        found = get_vehicle_by_registration_number('dl-05-xy-0001')
        self.assertIsNotNone(found)
        self.assertEqual(found.registration_number, 'DL-05-XY-0001')

        not_found = get_vehicle_by_registration_number('NON-EXISTENT')
        self.assertIsNone(not_found)

        empty_lookup = get_vehicle_by_registration_number('')
        self.assertIsNone(empty_lookup)

    def test_service_get_vehicle_by_plate_alias_for_member_3(self):
        Vehicle.objects.create(
            registration_number='KA-04-EV-8888',
            vehicle_type='EV Charging',
            owner=self.user,
        )
        found = get_vehicle_by_plate('  ka-04-ev-8888  ')
        self.assertIsNotNone(found)
        self.assertEqual(found.vehicle_type, 'EV Charging')

    def test_service_register_vehicle_success(self):
        v = register_vehicle(
            owner=self.user,
            registration_number='ka-02-bb-4321',
            vehicle_type='SUV',
            owner_name='Test Driver',
            owner_phone='9876543210',
        )
        self.assertEqual(v.registration_number, 'KA-02-BB-4321')
        self.assertEqual(v.owner, self.user)

    def test_service_register_vehicle_duplicate_raises_conflict(self):
        register_vehicle(
            owner=self.user,
            registration_number='KA-03-AA-1111',
            vehicle_type='Compact',
        )
        with self.assertRaises(Conflict) as ctx:
            register_vehicle(
                owner=self.other_user,
                registration_number='  ka-03-aa-1111  ',
                vehicle_type='Two-Wheeler',
            )
        self.assertIn('already exists', str(ctx.exception))

    def test_service_register_vehicle_invalid_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            register_vehicle(
                owner=self.user,
                registration_number='KA-03-AA-2222',
                vehicle_type='Spaceship',
            )

    def test_service_register_vehicle_missing_owner_raises_value_error(self):
        with self.assertRaises(ValueError):
            register_vehicle(
                owner=None,
                registration_number='KA-03-AA-3333',
                vehicle_type='Compact',
            )

    def test_service_register_vehicle_plate_too_long_raises_value_error(self):
        with self.assertRaises(ValueError):
            register_vehicle(
                owner=self.user,
                registration_number='A' * 21,
                vehicle_type='Compact',
            )

    def test_owner_can_register_multiple_distinct_vehicles(self):
        v1 = register_vehicle(self.user, 'KA-01-DISTINCT-1', 'Two-Wheeler')
        v2 = register_vehicle(self.user, 'KA-01-DISTINCT-2', 'Compact')
        self.assertEqual(Vehicle.objects.filter(owner=self.user).count(), 2)
        self.assertNotEqual(v1.id, v2.id)


class VehicleAPITests(TestCase):
    """API integration tests for Vehicle registration endpoint (TC-UC02-API-001)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='auth_customer',
            email='customer@parking.local',
            password='SecurePassword123!',
            role='Customer',
            status='active',
        )
        token = AccessToken.for_user(self.user)
        token['token_version'] = self.user.token_version
        token['username'] = self.user.username
        token['role'] = self.user.role
        self.token = str(token)
        self.endpoint_v1 = '/api/v1/vehicles/'
        self.endpoint_root = '/api/vehicles/'

    def test_unauthenticated_request_rejected_with_401(self):
        response = self.client.post(self.endpoint_v1, {
            'registration_number': 'KA-01-AB-1234',
            'vehicle_type': 'Compact',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertIn('code', data)
        self.assertEqual(data['code'], 'AUTHENTICATION_REQUIRED')

    def test_valid_vehicle_registration_returns_201_created(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        payload = {
            'registration_number': '  ka-05-jk-4567  ',
            'vehicle_type': 'Compact',
            'owner_name': 'Alice Walker',
            'owner_phone': '9876543210',
        }
        response = self.client.post(self.endpoint_v1, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['registration_number'], 'KA-05-JK-4567')
        self.assertEqual(data['vehicle_type'], 'Compact')
        self.assertEqual(data['owner'], self.user.id)
        self.assertEqual(data['owner_name'], 'Alice Walker')
        self.assertEqual(data['owner_phone'], '9876543210')
        self.assertIn('id', data)

        # Confirm database state
        db_vehicle = Vehicle.objects.get(registration_number='KA-05-JK-4567')
        self.assertEqual(db_vehicle.owner, self.user)

    def test_valid_registration_via_plate_number_alias_key(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        payload = {
            'plate_number': 'DL-01-ZZ-9999',
            'vehicle_type': 'Two-Wheeler',
        }
        response = self.client.post(self.endpoint_v1, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data['registration_number'], 'DL-01-ZZ-9999')

    def test_missing_registration_number_returns_400_validation_error(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.endpoint_v1, {
            'vehicle_type': 'Compact',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['code'], 'VALIDATION_ERROR')
        self.assertIn('registration_number', data['details'])

    def test_blank_registration_number_returns_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.endpoint_v1, {
            'registration_number': '   ',
            'vehicle_type': 'Compact',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['code'], 'VALIDATION_ERROR')
        self.assertIn('registration_number', data['details'])

    def test_registration_number_exceeding_max_length_returns_400(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.endpoint_v1, {
            'registration_number': 'A' * 21,
            'vehicle_type': 'Compact',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['code'], 'VALIDATION_ERROR')
        self.assertIn('registration_number', data['details'])

    def test_missing_vehicle_type_returns_400_validation_error(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.endpoint_v1, {
            'registration_number': 'MH-01-AA-1111',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['code'], 'VALIDATION_ERROR')
        self.assertIn('vehicle_type', data['details'])

    def test_invalid_vehicle_type_returns_400_validation_error(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.endpoint_v1, {
            'registration_number': 'MH-01-AA-1111',
            'vehicle_type': 'Spaceship',
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['code'], 'VALIDATION_ERROR')
        self.assertIn('vehicle_type', data['details'])

    def test_duplicate_registration_number_returns_409_conflict(self):
        Vehicle.objects.create(
            registration_number='KA-01-DUP-1111',
            vehicle_type='Compact',
            owner=self.user,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.endpoint_v1, {
            'registration_number': '  ka-01-dup-1111  ',
            'vehicle_type': 'SUV',
        })
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        data = response.json()
        self.assertEqual(data['code'], 'CONFLICT')
        self.assertIn('already exists', data['error'].lower())

    def test_ownership_cannot_be_spoofed_via_request_payload(self):
        victim = User.objects.create_user(
            username='victim_user',
            email='victim@parking.local',
            password='Password123!',
            role='Customer',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        payload = {
            'registration_number': 'KA-99-SPOOF-01',
            'vehicle_type': 'SUV',
            'owner': victim.id,
            'owner_id': victim.id,
            'user': victim.id,
        }
        response = self.client.post(self.endpoint_v1, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        # Must be assigned to self.user (authenticated caller), NOT victim
        self.assertEqual(data['owner'], self.user.id)
        saved = Vehicle.objects.get(registration_number='KA-99-SPOOF-01')
        self.assertEqual(saved.owner, self.user)

    def test_get_vehicles_returns_only_authenticated_user_vehicles(self):
        other_user = User.objects.create_user(
            username='other_user',
            email='other@parking.local',
            password='Password123!',
        )
        Vehicle.objects.create(
            registration_number='MY-VEHICLE-01',
            vehicle_type='Compact',
            owner=self.user,
        )
        Vehicle.objects.create(
            registration_number='THEIR-VEHICLE-02',
            vehicle_type='SUV',
            owner=other_user,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.endpoint_v1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['registration_number'], 'MY-VEHICLE-01')

    def test_endpoint_accessible_via_both_v1_and_root_routes(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        # POST to legacy /api/vehicles/
        res1 = self.client.post(self.endpoint_root, {
            'registration_number': 'KA-ROOT-1111',
            'vehicle_type': 'Two-Wheeler',
        })
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # GET from legacy /api/vehicles/
        res2 = self.client.get(self.endpoint_root)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        plates = [v['registration_number'] for v in res2.json()]
        self.assertIn('KA-ROOT-1111', plates)
