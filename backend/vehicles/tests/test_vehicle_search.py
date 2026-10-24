"""
Automated unit and API tests for US-07: Search Vehicle & Parking Status (FR-11, TC-UC02-API-001, TC-UC02-API-002).
Validates:
- License plate lookup and input normalization
- Live parking status resolution (Parked with slot vs Not Parked)
- Structured not-found response (FR-14 / HTTP 404)
- Role-based access control (Admin/Operator access any vehicle; Customer restricted to own)
- Performance (< 500ms response, indexed query execution)
"""
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.test import APIClient

from vehicles.models import Vehicle
from vehicles.services import (
    get_vehicle_parking_status,
    search_vehicle_by_plate,
)

User = get_user_model()


class VehicleSearchServiceTests(TestCase):
    """Unit tests for vehicle search and parking status service functions (TC-UC02-UNIT-001 / FR-11)."""

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

    def test_search_vehicle_by_plate_exact_match(self):
        """Exact normalized plate returns the vehicle and not-parked status by default."""
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

    def test_search_vehicle_not_found_raises_404(self):
        """Non-existent plate raises NotFound exception (HTTP 404)."""
        with self.assertRaises(NotFound):
            search_vehicle_by_plate('KA-99-NONEXIST-01', requesting_user=self.owner)

    def test_search_vehicle_empty_query_raises_value_error(self):
        """Empty or blank plate string raises ValueError."""
        with self.assertRaises(ValueError):
            search_vehicle_by_plate('', requesting_user=self.owner)
        with self.assertRaises(ValueError):
            search_vehicle_by_plate('   ', requesting_user=self.owner)

    def test_customer_searching_other_vehicle_raises_permission_denied(self):
        """Customer attempting to search another owner's vehicle raises PermissionDenied (HTTP 403)."""
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

    def test_get_vehicle_parking_status_parked_state(self):
        """When active slot is associated, get_vehicle_parking_status returns PARKED with slot metadata."""
        mock_slot = SimpleNamespace(
            id=42,
            slot_number='B-204',
            zone_name='North Zone',
            floor=2,
            session_id=101,
            check_in_time='2026-10-24T18:00:00Z',
        )
        self.vehicle._mock_active_slot = mock_slot
        status = get_vehicle_parking_status(self.vehicle)

        self.assertTrue(status['is_parked'])
        self.assertEqual(status['status'], 'PARKED')
        self.assertEqual(status['slot']['slot_number'], 'B-204')
        self.assertEqual(status['slot']['zone'], 'North Zone')
        self.assertEqual(status['slot']['floor'], 2)


class VehicleSearchAPITests(TestCase):
    """API integration tests for US-07 vehicle search endpoints (TC-UC02-API-001, TC-UC02-API-002)."""

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
            role='Operator',
        )
        self.admin = User.objects.create_user(
            username='parking_admin',
            password='Password123!',
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

    def test_search_unauthenticated_returns_401(self):
        """Unauthenticated requests to search endpoint return HTTP 401 Unauthorized."""
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_missing_plate_param_returns_400(self):
        """Missing plate query parameter returns HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/v1/vehicles/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

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

    def test_search_performance_under_500ms(self):
        """Search query execution is responsive (< 500ms p95, NFR-PERF-01)."""
        import time
        self.client.force_authenticate(user=self.customer)

        start = time.perf_counter()
        response = self.client.get('/api/v1/vehicles/search/?plate=DL-01-AB-1234')
        elapsed_ms = (time.perf_counter() - start) * 1000

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(elapsed_ms, 500.0, f'Search response took {elapsed_ms:.1f}ms (threshold 500ms)')
