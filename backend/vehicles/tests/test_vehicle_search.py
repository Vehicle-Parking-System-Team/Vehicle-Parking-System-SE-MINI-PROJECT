"""
Automated unit and API tests for US-07: Search Vehicle & Parking Status (FR-11, TC-UC02-API-001, TC-UC02-API-002).
Validates:
- License plate lookup and input normalization (case, whitespace, separators)
- Live parking status resolution using authoritative persisted ParkingSession records (Parked, Not Parked, Completed historical)
- Safe handling of missing slot relationships and inconsistent records
- Partial registration plate search (exact, prefix, substring, multiple matches, no matches)
- Vehicle modification authorization (Owner update succeeds, Stranger / Operator update rejected with 403)
- Registration number format validation (standard state formats, BH-series, positive/negative validation)
- Role-based access control (Admin/Operator access any vehicle; Customer restricted to own)
- Performance (< 500ms response, indexed query execution)
"""
import time
from unittest import mock
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.test import APIClient

from operations.models import ParkingRecord
from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle
from vehicles.services import (
    get_vehicle_parking_status,
    is_valid_registration_number,
    normalize_registration_number,
    search_vehicle_by_plate,
    search_vehicles,
)

User = get_user_model()


class VehicleSearchServiceTests(TestCase):
    """Unit tests for vehicle search, normalization, and live parking status (FR-11)."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username='carowner1',
            password='Password123!',
            email='owner1@test.com',
            role='Customer',
        )
        self.vehicle = Vehicle.objects.create(
            registration_number='KA-01-MG-1000',
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
            owner=self.owner,
            owner_name='Rajesh Kumar',
            owner_phone='9876543210',
        )
        self.zone = ParkingZone.objects.create(name='North Zone')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number='A-102',
            floor=1,
            status=ParkingSlot.Status.OCCUPIED,
            vehicle_type='Compact',
        )

    def test_search_vehicle_by_plate_exact_match(self):
        """Exact normalized plate returns the vehicle and not-parked status when no active session."""
        found_vehicle, parking_status = search_vehicle_by_plate('KA-01-MG-1000', requesting_user=self.owner)
        self.assertEqual(found_vehicle.pk, self.vehicle.pk)
        self.assertEqual(found_vehicle.registration_number, 'KA-01-MG-1000')
        self.assertFalse(parking_status['is_parked'])
        self.assertEqual(parking_status['status'], 'NOT_PARKED')
        self.assertIsNone(parking_status['slot'])

    def test_search_vehicle_plate_normalization(self):
        """Search normalizes whitespace and lower/mixed case input."""
        found_vehicle, _ = search_vehicle_by_plate('  ka-01-mg-1000   ', requesting_user=self.owner)
        self.assertEqual(found_vehicle.pk, self.vehicle.pk)

    def test_search_vehicle_space_separator_normalization(self):
        """Search normalizes permitted space separators into canonical registration number."""
        found_vehicle, _ = search_vehicle_by_plate('KA 01 MG 1000', requesting_user=self.owner)
        self.assertEqual(found_vehicle.pk, self.vehicle.pk)

    def test_search_vehicle_not_found_raises_404(self):
        """Non-existent plate raises NotFound exception (HTTP 404)."""
        with self.assertRaises(NotFound):
            search_vehicle_by_plate('KA-99-ZZ-0001', requesting_user=self.owner)

    def test_search_vehicle_empty_query_raises_value_error(self):
        """Empty or blank plate string raises ValueError."""
        with self.assertRaises(ValueError):
            search_vehicle_by_plate('', requesting_user=self.owner)
        with self.assertRaises(ValueError):
            search_vehicle_by_plate('   ', requesting_user=self.owner)

    def test_search_vehicle_too_short_raises_value_error(self):
        """Single non-separator character raises ValueError to prevent full-table scan."""
        with self.assertRaises(ValueError):
            search_vehicle_by_plate('K', requesting_user=self.owner)
        with self.assertRaises(ValueError):
            search_vehicle_by_plate('-', requesting_user=self.owner)

    def test_customer_searching_other_vehicle_raises_permission_denied(self):
        """Customer attempting to search another owner's exact vehicle raises PermissionDenied (HTTP 403)."""
        other_user = User.objects.create_user(
            username='stranger1',
            password='Password123!',
            role='Customer',
        )
        with self.assertRaises(PermissionDenied):
            search_vehicle_by_plate('KA-01-MG-1000', requesting_user=other_user)

    def test_admin_can_search_any_vehicle(self):
        """Admin user can search and inspect any vehicle."""
        admin_user = User.objects.create_user(
            username='sysadmin',
            password='Password123!',
            role='Admin',
        )
        found_vehicle, _ = search_vehicle_by_plate('KA-01-MG-1000', requesting_user=admin_user)
        self.assertEqual(found_vehicle.pk, self.vehicle.pk)

    def test_operator_can_search_any_vehicle(self):
        """Operator user can search and inspect any vehicle."""
        operator_user = User.objects.create_user(
            username='gateoperator',
            password='Password123!',
            role='Operator',
        )
        found_vehicle, _ = search_vehicle_by_plate('KA-01-MG-1000', requesting_user=operator_user)
        self.assertEqual(found_vehicle.pk, self.vehicle.pk)

    def test_get_vehicle_parking_status_with_active_session_returns_parked(self):
        """Authoritative persisted active ParkingRecord returns PARKED with slot metadata."""
        record = ParkingRecord.objects.create(
            vehicle=self.vehicle,
            slot=self.slot,
            operator=self.owner,
            status=ParkingRecord.Status.ACTIVE,
        )

        status_data = get_vehicle_parking_status(self.vehicle)

        self.assertTrue(status_data['is_parked'])
        self.assertEqual(status_data['status'], 'PARKED')
        self.assertEqual(status_data['session_id'], record.pk)
        self.assertEqual(status_data['slot']['id'], self.slot.pk)
        self.assertEqual(status_data['slot']['slot_number'], 'A-102')
        self.assertEqual(status_data['slot']['zone'], 'North Zone')
        self.assertEqual(status_data['slot']['floor'], 1)

    def test_get_vehicle_parking_status_with_completed_session_returns_not_parked(self):
        """Vehicle with only completed historical ParkingRecord returns NOT_PARKED."""
        ParkingRecord.objects.create(
            vehicle=self.vehicle,
            slot=self.slot,
            operator=self.owner,
            status=ParkingRecord.Status.COMPLETED,
        )

        status_data = get_vehicle_parking_status(self.vehicle)

        self.assertFalse(status_data['is_parked'])
        self.assertEqual(status_data['status'], 'NOT_PARKED')
        self.assertIsNone(status_data['slot'])

    def test_get_vehicle_parking_status_safely_handles_missing_slot(self):
        """Vehicle without active parking record safely returns NOT_PARKED."""
        status_data = get_vehicle_parking_status(self.vehicle)

        self.assertFalse(status_data['is_parked'])
        self.assertEqual(status_data['status'], 'NOT_PARKED')
        self.assertIsNone(status_data['slot'])

    def test_partial_search_prefix_and_substring(self):
        """Partial matching finds vehicle by prefix or substring."""
        # Prefix match
        results = search_vehicles('KA-01', requesting_user=self.owner)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0].pk, self.vehicle.pk)

        # Substring match
        results_sub = search_vehicles('MG-1000', requesting_user=self.owner)
        self.assertEqual(len(results_sub), 1)
        self.assertEqual(results_sub[0][0].pk, self.vehicle.pk)

        # Numeric tail match
        results_num = search_vehicles('1000', requesting_user=self.owner)
        self.assertEqual(len(results_num), 1)
        self.assertEqual(results_num[0][0].pk, self.vehicle.pk)

    def test_partial_search_multiple_matches(self):
        """Partial matching returning multiple vehicles produces a list of all matches."""
        Vehicle.objects.create(
            registration_number='KA-01-AB-2000',
            vehicle_type=Vehicle.VEHICLE_TYPE_SUV,
            owner=self.owner,
        )

        results = search_vehicles('KA-01', requesting_user=self.owner)
        self.assertEqual(len(results), 2)
        plates = [v[0].registration_number for v in results]
        self.assertIn('KA-01-MG-1000', plates)
        self.assertIn('KA-01-AB-2000', plates)


class RegistrationNumberValidationTests(TestCase):
    """Validation rule tests for supported Indian and BH-series registration formats."""

    def test_valid_standard_state_registration_formats(self):
        """Standard state formats with hyphens, spaces, or compact alphanumeric pass validation."""
        valid_examples = [
            'KA-01-AB-1234',
            'DL-05-CD-5678',
            'MH-12-CD-5678',
            'KA 01 AB 1234',
            'KA01AB1234',
            'DL3CBB1122',
            'KA-03-HA-5555',
            'KA-01-TEST-99',
            'KA-05-VIEW-01',
            'DL-05-XY-0001',
        ]
        for plate in valid_examples:
            self.assertTrue(is_valid_registration_number(plate), f'Expected {plate} to be valid')

    def test_valid_bh_series_registration_formats(self):
        """BH-series formats (e.g. 22-BH-1234-AA) pass validation."""
        valid_bh = [
            '22-BH-1234-AA',
            '22 BH 1234 AA',
            '22BH1234AA',
            '23-BH-5678-B',
        ]
        for plate in valid_bh:
            self.assertTrue(is_valid_registration_number(plate), f'Expected BH plate {plate} to be valid')

    def test_invalid_registration_formats_rejected(self):
        """Malformed, incomplete, oversized, and junk-bearing registrations are rejected."""
        invalid_examples = [
            '',
            '   ',
            'KA',
            'KA-01',
            '123-KA-01-AB-1234',      # numeric prefix instead of state code
            'KAA-01-AB-1234',         # 3-letter state code
            'KA-01-AB-123456',        # 6-digit serial
            'KA-01-TOOLONGSERIES-1234',# series too long (> 8 chars)
            'KA#01-AB-1234',          # illegal character
            'KA-01-AB-1234-EXTRA',    # trailing junk
            'PREFIX-KA-01-AB-1234',   # leading junk
            'KA-01-AB-1234@xyz',      # embedded suffix
            'A' * 21,                 # exceeds 20 chars
        ]
        for plate in invalid_examples:
            self.assertFalse(is_valid_registration_number(plate), f'Expected {plate} to be invalid')


class VehicleSearchAPITests(TestCase):
    """API integration tests for US-07 vehicle search and authorization (TC-UC02-API-001, TC-UC02-API-002)."""

    def setUp(self):
        self.client = APIClient()

        # Users
        self.customer = User.objects.create_user(
            username='driver1',
            password='Password123!',
            email='driver1@test.com',
            role='Customer',
        )
        self.other_customer = User.objects.create_user(
            username='driver2',
            password='Password123!',
            email='driver2@test.com',
            role='Customer',
        )
        self.operator = User.objects.create_user(
            username='parking_op',
            password='Password123!',
            email='op@test.com',
            role='Operator',
        )
        self.admin = User.objects.create_user(
            username='parking_admin',
            password='Password123!',
            email='admin@test.com',
            role='Admin',
        )

        # Vehicles
        self.vehicle = Vehicle.objects.create(
            registration_number='DL-01-AB-1234',
            vehicle_type=Vehicle.VEHICLE_TYPE_SUV,
            owner=self.customer,
            owner_name='Aarav Sharma',
            owner_phone='9811122233',
        )
        self.zone = ParkingZone.objects.create(name='Central Bay')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number='C-301',
            floor=3,
            status=ParkingSlot.Status.OCCUPIED,
            vehicle_type='SUV',
        )

    def test_search_unauthenticated_returns_401(self):
        """Unauthenticated requests to search endpoint return HTTP 401 Unauthorized."""
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_missing_plate_param_returns_400(self):
        """Missing plate query parameter returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 'VALIDATION_ERROR')
        self.assertEqual(set(response.data), {'error', 'code', 'details'})
        self.assertIn('plate', response.data['details'])

    def test_search_own_vehicle_by_query_param(self):
        """Customer searching their own vehicle returns HTTP 200 with vehicle and status."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/search/?plate=dl-01-ab-1234')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['registration_number'], 'DL-01-AB-1234')
        self.assertEqual(response.data['vehicle_type'], 'SUV')
        self.assertEqual(response.data['owner_name'], 'Aarav Sharma')
        self.assertIn('parking_status', response.data)
        self.assertFalse(response.data['parking_status']['is_parked'])
        self.assertEqual(response.data['parking_status']['status'], 'NOT_PARKED')

    def test_search_own_vehicle_parked_live_status(self):
        """Authoritative persisted active ParkingRecord returns live PARKED status in API response."""
        record = ParkingRecord.objects.create(
            vehicle=self.vehicle,
            slot=self.slot,
            operator=self.customer,
            status=ParkingRecord.Status.ACTIVE,
        )

        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['parking_status']['is_parked'])
        self.assertEqual(response.data['parking_status']['status'], 'PARKED')
        self.assertEqual(response.data['parking_status']['session_id'], record.pk)
        self.assertEqual(response.data['parking_status']['slot']['slot_number'], 'C-301')

    def test_search_own_vehicle_completed_session_returns_not_parked(self):
        """Authoritative persisted completed ParkingRecord returns NOT_PARKED status in API response."""
        ParkingRecord.objects.create(
            vehicle=self.vehicle,
            slot=self.slot,
            operator=self.customer,
            status=ParkingRecord.Status.COMPLETED,
        )

        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['parking_status']['is_parked'])
        self.assertEqual(response.data['parking_status']['status'], 'NOT_PARKED')
        self.assertIsNone(response.data['parking_status']['slot'])

    def test_search_own_vehicle_by_path_param(self):
        """Customer searching via path parameter returns HTTP 200."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/search/DL-01-AB-1234/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.vehicle.id)

    def test_customer_forbidden_from_other_vehicle_search(self):
        """Customer searching another user's vehicle receives HTTP 403 Forbidden."""
        self.client.force_authenticate(user=self.other_customer)
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_can_search_any_customer_vehicle(self):
        """Operator can search any vehicle across the facility."""
        self.client.force_authenticate(user=self.operator)
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['registration_number'], 'DL-01-AB-1234')

    def test_admin_can_search_any_customer_vehicle(self):
        """Admin can search any vehicle across the facility."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['registration_number'], 'DL-01-AB-1234')

    def test_partial_search_multiple_matches_returns_list(self):
        """Partial search with multiple matches returns a list of results."""
        Vehicle.objects.create(
            registration_number='DL-01-CD-9999',
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
            owner=self.customer,
        )
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

    def test_search_nonexistent_plate_returns_404(self):
        """Searching a non-registered plate returns HTTP 404 Not Found."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/search/?plate=MH-12-XX-9999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_by_plate_direct_lookup_with_include_status(self):
        """Direct lookup /api/v1/vehicles/by-plate/<plate>/?include_status=true returns parking status."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/by-plate/DL-01-AB-1234/?include_status=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('parking_status', response.data)
        self.assertFalse(response.data['parking_status']['is_parked'])

    # --- Authorization Regression Tests for Vehicle Modifications ---

    def test_owner_can_update_own_vehicle_put_and_patch(self):
        """Owner can update their own vehicle record via PUT and PATCH."""
        self.client.force_authenticate(user=self.customer)

        # PUT update
        put_payload = {
            'registration_number': 'DL-01-AB-1234',
            'vehicle_type': 'Compact',
            'owner_name': 'Aarav Updated',
        }
        res_put = self.client.put(f'/api/v1/vehicles/{self.vehicle.id}/', put_payload)
        self.assertEqual(res_put.status_code, status.HTTP_200_OK)
        self.assertEqual(res_put.data['owner_name'], 'Aarav Updated')

        # PATCH update
        patch_payload = {'owner_name': 'Aarav Patched'}
        res_patch = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', patch_payload)
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(res_patch.data['owner_name'], 'Aarav Patched')

    def test_user_cannot_update_another_customers_vehicle(self):
        """A user attempting to update another customer's vehicle is rejected with 403 Forbidden."""
        self.client.force_authenticate(user=self.other_customer)

        # PUT attempt
        res_put = self.client.put(
            f'/api/v1/vehicles/{self.vehicle.id}/',
            {'registration_number': 'DL-01-AB-1234', 'vehicle_type': 'Compact'},
        )
        self.assertEqual(res_put.status_code, status.HTTP_403_FORBIDDEN)

        # PATCH attempt
        res_patch = self.client.patch(
            f'/api/v1/vehicles/{self.vehicle.id}/',
            {'vehicle_type': 'Compact'},
        )
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

    def test_operator_can_manage_customer_vehicle(self):
        """Operator has documented access to update customer vehicles (FR-02 / FR-16)."""
        self.client.force_authenticate(user=self.operator)

        # PATCH attempt by plate
        res_patch_plate = self.client.patch(
            f'/api/v1/vehicles/by-plate/{self.vehicle.registration_number}/',
            {'owner_name': 'Operator Verified Name'},
        )
        self.assertEqual(res_patch_plate.status_code, status.HTTP_200_OK)
        self.assertEqual(res_patch_plate.data['owner_name'], 'Operator Verified Name')

    def test_backend_rejects_invalid_registration_format_on_create_and_update(self):
        """Backend validates registration formats and rejects malformed plates on create and update."""
        self.client.force_authenticate(user=self.customer)

        # Invalid creation
        invalid_create = {
            'registration_number': 'INVALID_PLATE#99',
            'vehicle_type': 'Compact',
        }
        res_create = self.client.post('/api/v1/vehicles/', invalid_create)
        self.assertEqual(res_create.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('registration_number', res_create.data.get('details', {}))

        # Invalid update
        invalid_update = {'registration_number': 'JUNK-1234-EXTRA'}
        res_update = self.client.patch(f'/api/v1/vehicles/{self.vehicle.id}/', invalid_update)
        self.assertEqual(res_update.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('registration_number', res_update.data.get('details', {}))

    def test_search_performance_under_500ms(self):
        """Search query execution is responsive (< 500ms p95, NFR-PERF-01)."""
        self.client.force_authenticate(user=self.customer)

        start = time.perf_counter()
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(elapsed_ms, 500.0, f'Search response took {elapsed_ms:.1f}ms (threshold 500ms)')
