"""
Automated unit and API tests for US-06: Vehicle Profile & Update (FR-02, TC-UC02-API-002).
Tests retrieval by ID and plate, profile updates (PUT and PATCH), ownership isolation,
duplicate conflict handling, immutability of owner, and US-31 error compliance.
"""

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from common.exceptions import Conflict
from vehicles.models import Vehicle
from vehicles.services import (
    get_vehicle_by_id,
    get_vehicle_by_plate,
    register_vehicle,
    update_vehicle,
)

User = get_user_model()


class VehicleProfileServiceTests(TestCase):
    """Unit tests for vehicle profile retrieval and service update functions (FR-02 / US-06)."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='profile_owner',
            email='profile_owner@parking.local',
            password='Password123!',
            role='Customer',
        )
        self.other_user = User.objects.create_user(
            username='other_owner',
            email='other_owner@parking.local',
            password='Password123!',
            role='Customer',
        )
        self.vehicle = register_vehicle(
            owner=self.owner,
            registration_number='KA-01-MJ-1001',
            vehicle_type='Compact',
            owner_name='Original Name',
            owner_phone='9876543210',
        )

    def test_get_vehicle_by_id_returns_vehicle(self):
        found = get_vehicle_by_id(self.vehicle.id)
        self.assertIsNotNone(found)
        self.assertEqual(found.id, self.vehicle.id)
        self.assertEqual(found.registration_number, 'KA-01-MJ-1001')

    def test_get_vehicle_by_id_returns_none_for_missing(self):
        self.assertIsNone(get_vehicle_by_id(999999))

    def test_get_vehicle_by_id_returns_none_for_invalid(self):
        self.assertIsNone(get_vehicle_by_id('invalid'))

    def test_update_vehicle_service_success(self):
        updated = update_vehicle(
            vehicle=self.vehicle,
            registration_number='ka-01-mj-1002',
            vehicle_type='SUV',
            owner_name='Updated Name',
            owner_phone='9123456789',
        )
        self.assertEqual(updated.registration_number, 'KA-01-MJ-1002')
        self.assertEqual(updated.vehicle_type, 'SUV')
        self.assertEqual(updated.owner_name, 'Updated Name')
        self.assertEqual(updated.owner_phone, '9123456789')

        refreshed = Vehicle.objects.get(pk=self.vehicle.pk)
        self.assertEqual(refreshed.registration_number, 'KA-01-MJ-1002')
        self.assertEqual(refreshed.vehicle_type, 'SUV')

    def test_update_vehicle_service_same_plate_succeeds(self):
        # Updating details with the exact same plate must not trigger conflict
        updated = update_vehicle(
            vehicle=self.vehicle,
            registration_number='KA-01-MJ-1001',
            owner_name='New Contact Name',
        )
        self.assertEqual(updated.owner_name, 'New Contact Name')
        self.assertEqual(updated.registration_number, 'KA-01-MJ-1001')

    def test_update_vehicle_service_duplicate_plate_raises_conflict(self):
        register_vehicle(
            owner=self.other_user,
            registration_number='KA-02-OTHER-99',
            vehicle_type='Two-Wheeler',
        )
        with self.assertRaises(Conflict):
            update_vehicle(
                vehicle=self.vehicle,
                registration_number='ka-02-other-99',
            )

    def test_update_vehicle_service_invalid_type_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            update_vehicle(self.vehicle, vehicle_type='Truck')
        self.assertIn('Invalid vehicle type', str(ctx.exception))

    def test_update_vehicle_service_invalid_plate_raises_value_error(self):
        with self.assertRaises(ValueError):
            update_vehicle(self.vehicle, registration_number='')

        with self.assertRaises(ValueError):
            update_vehicle(self.vehicle, registration_number='A' * 25)


class VehicleProfileAPITests(TestCase):
    """API integration tests for Vehicle profile view and update endpoints (TC-UC02-API-002)."""

    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='car_owner',
            email='car_owner@parking.local',
            password='SecurePassword123!',
            role='Customer',
            status='active',
        )
        self.other_user = User.objects.create_user(
            username='stranger_user',
            email='stranger@parking.local',
            password='SecurePassword123!',
            role='Customer',
            status='active',
        )

        # Create JWT tokens
        token_owner = AccessToken.for_user(self.owner)
        token_owner['token_version'] = self.owner.token_version
        token_owner['username'] = self.owner.username
        token_owner['role'] = self.owner.role
        self.owner_token = str(token_owner)

        token_stranger = AccessToken.for_user(self.other_user)
        token_stranger['token_version'] = self.other_user.token_version
        token_stranger['username'] = self.other_user.username
        token_stranger['role'] = self.other_user.role
        self.stranger_token = str(token_stranger)

        self.vehicle = Vehicle.objects.create(
            registration_number='KA-03-HA-5555',
            vehicle_type='Compact',
            owner=self.owner,
            owner_name='Car Owner',
            owner_phone='9876500000',
        )

    def test_unauthenticated_requests_rejected(self):
        url = f'/api/v1/vehicles/{self.vehicle.id}/'
        # GET
        res = self.client.get(url)
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # PUT
        res = self.client.put(url, {'registration_number': 'KA-03-HA-5555', 'vehicle_type': 'Compact'})
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # PATCH
        res = self.client.patch(url, {'vehicle_type': 'SUV'})
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_get_vehicle_by_id_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        res = self.client.get(f'/api/v1/vehicles/{self.vehicle.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], self.vehicle.id)
        self.assertEqual(res.data['registration_number'], 'KA-03-HA-5555')
        self.assertEqual(res.data['vehicle_type'], 'Compact')
        self.assertEqual(res.data['owner_name'], 'Car Owner')
        self.assertEqual(res.data['owner_phone'], '9876500000')
        self.assertEqual(res.data['owner_username'], self.owner.username)

    def test_get_vehicle_by_plate_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        res = self.client.get(f'/api/v1/vehicles/by-plate/{self.vehicle.registration_number}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], self.vehicle.id)
        self.assertEqual(res.data['registration_number'], 'KA-03-HA-5555')

    def test_get_vehicle_by_id_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        res = self.client.get('/api/v1/vehicles/99999/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data['code'], 'NOT_FOUND')

    def test_get_vehicle_by_plate_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        res = self.client.get('/api/v1/vehicles/by-plate/NONEXISTENT-PLATE/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data['code'], 'NOT_FOUND')

    def test_other_user_cannot_view_vehicle(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        res = self.client.get(f'/api/v1/vehicles/{self.vehicle.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.data['code'], 'PERMISSION_DENIED')

    def test_put_full_update_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {
            'registration_number': 'KA-03-HA-9999',
            'vehicle_type': 'SUV',
            'owner_name': 'Updated Car Owner',
            'owner_phone': '9111222333',
        }
        res = self.client.put(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['registration_number'], 'KA-03-HA-9999')
        self.assertEqual(res.data['vehicle_type'], 'SUV')
        self.assertEqual(res.data['owner_name'], 'Updated Car Owner')
        self.assertEqual(res.data['owner_phone'], '9111222333')

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.registration_number, 'KA-03-HA-9999')
        self.assertEqual(self.vehicle.vehicle_type, 'SUV')

    def test_patch_partial_update_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {
            'vehicle_type': 'Two-Wheeler',
            'owner_phone': '9555666777',
        }
        res = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['vehicle_type'], 'Two-Wheeler')
        self.assertEqual(res.data['owner_phone'], '9555666777')
        self.assertEqual(res.data['registration_number'], 'KA-03-HA-5555')

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.vehicle_type, 'Two-Wheeler')
        self.assertEqual(self.vehicle.owner_phone, '9555666777')
        self.assertEqual(self.vehicle.registration_number, 'KA-03-HA-5555')

    def test_patch_with_same_plate_does_not_conflict(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {
            'registration_number': 'ka-03-ha-5555',
            'owner_name': 'Same Plate New Name',
        }
        res = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['owner_name'], 'Same Plate New Name')

    def test_update_duplicate_plate_conflict_returns_409(self):
        # Create a second vehicle owned by another user
        Vehicle.objects.create(
            registration_number='DL-01-TAKEN-1',
            vehicle_type='Compact',
            owner=self.other_user,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {'registration_number': 'dl-01-taken-1'}
        res = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(res.data['code'], 'CONFLICT')
        self.assertIn('already exists', res.data['error'])

    def test_other_user_cannot_update_vehicle(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        payload = {'vehicle_type': 'SUV', 'owner_name': 'Hacker'}
        res = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.data['code'], 'PERMISSION_DENIED')

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.vehicle_type, 'Compact')
        self.assertEqual(self.vehicle.owner_name, 'Car Owner')

    def test_update_non_existent_vehicle_returns_404(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {'vehicle_type': 'SUV'}
        res = self.client.patch('/api/v1/vehicles/99999/', payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(res.data['code'], 'NOT_FOUND')

    def test_invalid_payload_rejected_with_400_validation_error(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        # Invalid vehicle type
        res = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', {'vehicle_type': 'Airplane'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')
        self.assertIn('vehicle_type', res.data['details'])

        # Overly long plate (>20 chars)
        res = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', {'registration_number': 'A' * 25})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')
        self.assertIn('registration_number', res.data['details'])

    def test_owner_field_cannot_be_tampered_via_update(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {
            'owner': self.other_user.id,
            'owner_name': 'Hijacked Owner',
        }
        res = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.owner, self.owner)

    def test_put_missing_registration_number_returns_400_validation_error(self):
        """Full PUT update omitting registration_number is rejected with 400 and not treated as PATCH."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {
            'vehicle_type': 'SUV',
            'owner_name': 'Attempted Partial via PUT',
        }
        res = self.client.put(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')
        self.assertIn('registration_number', res.data['details'])

        # Ensure vehicle state was not modified
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.vehicle_type, 'Compact')
        self.assertEqual(self.vehicle.owner_name, 'Car Owner')

    def test_put_missing_vehicle_type_returns_400_validation_error(self):
        """Full PUT update omitting required vehicle_type is rejected with 400 validation error."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {
            'registration_number': 'KA-03-HA-5555',
            'owner_name': 'Car Owner',
        }
        res = self.client.put(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')
        self.assertIn('vehicle_type', res.data['details'])

    def test_put_missing_all_required_fields_returns_400_validation_error(self):
        """Full PUT update with empty payload returns structured 400 validation error."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        res = self.client.put(f'/api/v1/vehicles/{self.vehicle.id}/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')
        self.assertIn('vehicle_type', res.data['details'])

    def test_put_with_plate_number_alias_succeeds(self):
        """Full PUT update providing plate_number alias instead of registration_number succeeds."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        payload = {
            'plate_number': 'ka-03-ha-7777',
            'vehicle_type': 'SUV',
            'owner_name': 'Updated via Alias',
        }
        res = self.client.put(f'/api/v1/vehicles/{self.vehicle.id}/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['registration_number'], 'KA-03-HA-7777')
        self.assertEqual(res.data['vehicle_type'], 'SUV')

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.registration_number, 'KA-03-HA-7777')

    def test_patch_omitting_plate_preserves_registration_number(self):
        """Partial PATCH updating only classification or contact preserves existing plate."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        res = self.client.patch(
            f'/api/v1/vehicles/{self.vehicle.id}/',
            {'vehicle_type': 'EV Charging'},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['vehicle_type'], 'EV Charging')
        self.assertEqual(res.data['registration_number'], 'KA-03-HA-5555')

        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.vehicle_type, 'EV Charging')
        self.assertEqual(self.vehicle.registration_number, 'KA-03-HA-5555')

    def test_other_user_cannot_view_vehicle_by_plate(self):
        """Customer cannot view another user's vehicle via the plate route (anti-enumeration)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        res = self.client.get(f'/api/v1/vehicles/by-plate/{self.vehicle.registration_number}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.data['code'], 'PERMISSION_DENIED')
        # Ensure no private vehicle information leaks in error response
        self.assertEqual(res.data.get('details'), {})
        self.assertNotIn('registration_number', res.data)
        self.assertNotIn('owner_name', res.data)

    def test_other_user_cannot_update_vehicle_by_plate(self):
        """Customer cannot update another user's vehicle via the plate route."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        res = self.client.put(
            f'/api/v1/vehicles/by-plate/{self.vehicle.registration_number}/',
            {'registration_number': 'KA-03-HA-5555', 'vehicle_type': 'SUV'},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.data['code'], 'PERMISSION_DENIED')

        res_patch = self.client.patch(
            f'/api/v1/vehicles/by-plate/{self.vehicle.registration_number}/',
            {'vehicle_type': 'SUV'},
        )
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res_patch.data['code'], 'PERMISSION_DENIED')

    def test_admin_and_operator_roles_can_access_vehicle_by_id_and_plate(self):
        """Admin and Operator roles retain documented access to inspect and manage vehicles (FR-02 / FR-16)."""
        admin_user = User.objects.create_user(
            username='admin_inspector',
            email='admin_inspector@parking.local',
            password='SecurePassword123!',
            role='Admin',
            status='active',
        )
        operator_user = User.objects.create_user(
            username='operator_inspector',
            email='operator_inspector@parking.local',
            password='SecurePassword123!',
            role='Operator',
            status='active',
        )

        admin_token = AccessToken.for_user(admin_user)
        admin_token['token_version'] = admin_user.token_version
        admin_token['username'] = admin_user.username
        admin_token['role'] = admin_user.role

        operator_token = AccessToken.for_user(operator_user)
        operator_token['token_version'] = operator_user.token_version
        operator_token['username'] = operator_user.username
        operator_token['role'] = operator_user.role

        # Admin access by ID
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(admin_token)}')
        res = self.client.get(f'/api/v1/vehicles/{self.vehicle.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], self.vehicle.id)

        # Admin access by plate
        res = self.client.get(f'/api/v1/vehicles/by-plate/{self.vehicle.registration_number}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['registration_number'], self.vehicle.registration_number)

        # Operator access by ID
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(operator_token)}')
        res = self.client.get(f'/api/v1/vehicles/{self.vehicle.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], self.vehicle.id)

        # Operator access by plate
        res = self.client.get(f'/api/v1/vehicles/by-plate/{self.vehicle.registration_number}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['registration_number'], self.vehicle.registration_number)

        # Operator update by plate
        res = self.client.patch(
            f'/api/v1/vehicles/by-plate/{self.vehicle.registration_number}/',
            {'owner_name': 'Operator Verified Name'},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['owner_name'], 'Operator Verified Name')
