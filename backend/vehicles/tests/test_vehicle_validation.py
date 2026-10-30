"""
US-08 vehicle payload validation and duplicate-handling regression tests.
Covers FR-13/FR-14 at service, serializer/API, and persistence boundaries.
"""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from vehicles.models import Vehicle
from vehicles.services import (
    is_registration_number_unique_violation,
    is_valid_registration_number,
    normalize_registration_number,
)

User = get_user_model()


class VehicleValidationServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='us08_owner',
            email='us08-owner@parking.local',
            password='Password123!',
            role='Customer',
        )

    def test_supported_plate_formats_normalize_to_one_canonical_value(self):
        self.assertEqual(normalize_registration_number('  ka 01 ab 1234 '), 'KA-01-AB-1234')
        self.assertEqual(normalize_registration_number('KA - 01 - AB - 1234'), 'KA-01-AB-1234')
        self.assertEqual(normalize_registration_number('dl3cbb1122'), 'DL3CBB1122')
        self.assertEqual(normalize_registration_number('22 bh 1234 aa'), '22-BH-1234-AA')

    def test_valid_supported_state_and_bh_formats(self):
        for plate in (
            'KA-01-AB-1234',
            'KA01AB1234',
            'KA-ROOT-1111',
            'DL3CBB1122',
            '22-BH-1234-AA',
            '22BH1234A',
        ):
            with self.subTest(plate=plate):
                self.assertTrue(is_valid_registration_number(plate))

    def test_invalid_characters_and_malformed_separators_are_not_sanitized(self):
        for plate in (
            'KA/01/AB/1234',
            'KA--01-AB-1234',
            'KA-01 AB-1234',
            'KA-01-AB-12345',
            'KA-01-AB-1234<script>',
            'KA\t01\tAB\t1234',
            'KA-01-AB',
            '1234',
        ):
            with self.subTest(plate=plate):
                self.assertFalse(is_valid_registration_number(plate))

    def test_non_string_values_are_not_coerced_into_registration_numbers(self):
        self.assertEqual(normalize_registration_number(12345), '')
        self.assertFalse(is_valid_registration_number(12345))

    def test_only_registration_unique_constraint_is_classified_as_duplicate(self):
        Vehicle.objects.create(
            registration_number='KA-01-UNIQ-01',
            vehicle_type='Compact',
            owner=self.owner,
        )
        with self.assertRaises(IntegrityError) as caught:
            with transaction.atomic():
                Vehicle.objects.create(
                    registration_number='KA-01-UNIQ-01',
                    vehicle_type='SUV',
                    owner=self.owner,
                )
        self.assertTrue(is_registration_number_unique_violation(caught.exception))
        self.assertFalse(is_registration_number_unique_violation(IntegrityError('foreign key constraint failed')))


class VehicleValidationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            username='us08_api_owner',
            email='us08-api-owner@parking.local',
            password='Password123!',
            role='Customer',
            status='active',
        )
        self.other_owner = User.objects.create_user(
            username='us08_other_owner',
            email='us08-api-other@parking.local',
            password='Password123!',
            role='Customer',
            status='active',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token(self.owner)}')
        self.endpoint = '/api/v1/vehicles/'

    @staticmethod
    def _token(user):
        token = AccessToken.for_user(user)
        token['token_version'] = user.token_version
        token['username'] = user.username
        token['role'] = user.role
        return str(token)

    def _assert_validation_error(self, response, field):
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body['code'], 'VALIDATION_ERROR')
        self.assertEqual(set(body), {'error', 'code', 'details'})
        self.assertIn(field, body['details'])
        self.assertTrue(body['error'])

    def test_invalid_plate_payloads_return_field_specific_400(self):
        for plate in (
            'KA/01/AB/1234',
            'KA--01-AB-1234',
            'KA-01 AB-1234',
            'KA-01-AB-12345',
            'KA-01-AB-1234<script>',
        ):
            with self.subTest(plate=plate):
                response = self.client.post(self.endpoint, {
                    'registration_number': plate,
                    'vehicle_type': 'Compact',
                }, format='json')
                self._assert_validation_error(response, 'registration_number')
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_missing_blank_and_overlong_plate_return_400(self):
        for payload in (
            {'vehicle_type': 'Compact'},
            {'registration_number': '   ', 'vehicle_type': 'Compact'},
            {'registration_number': 'A' * 21, 'vehicle_type': 'Compact'},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(self.endpoint, payload, format='json')
                self._assert_validation_error(response, 'registration_number')

    def test_valid_space_compact_and_bh_plates_are_sanitized_before_persistence(self):
        cases = (
            ('KA 01 AB 1234', 'KA-01-AB-1234', 'registration_number'),
            ('dl3cbb1122', 'DL3CBB1122', 'plate_number'),
            ('22 bh 1234 aa', '22-BH-1234-AA', 'registration_number'),
        )
        for input_plate, expected, field in cases:
            with self.subTest(input_plate=input_plate):
                response = self.client.post(self.endpoint, {
                    field: input_plate,
                    'vehicle_type': 'Compact',
                    'owner_name': '  Test Owner  ',
                    'owner_phone': '  9876543210  ',
                }, format='json')
                self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
                self.assertEqual(response.data['registration_number'], expected)
                self.assertEqual(response.data['owner_name'], 'Test Owner')
                self.assertEqual(response.data['owner_phone'], '9876543210')
        self.assertEqual(Vehicle.objects.count(), 3)

    def test_duplicate_normalized_plate_returns_structured_409_across_owners(self):
        Vehicle.objects.create(
            registration_number='KA-01-DUP-1234',
            vehicle_type='Compact',
            owner=self.owner,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._token(self.other_owner)}')
        response = self.client.post(self.endpoint, {
            'registration_number': 'ka 01 dup 1234',
            'vehicle_type': 'SUV',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, {
            'error': 'A vehicle with this registration number already exists.',
            'code': 'CONFLICT',
            'details': {},
        })
        self.assertEqual(Vehicle.objects.filter(registration_number='KA-01-DUP-1234').count(), 1)

    def test_conflicting_plate_aliases_return_field_specific_400(self):
        response = self.client.post(self.endpoint, {
            'registration_number': 'KA-01-AB-1234',
            'plate_number': 'KA-01-CD-5678',
            'vehicle_type': 'Compact',
        }, format='json')
        self._assert_validation_error(response, 'registration_number')
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_unknown_payload_fields_are_rejected_without_writing(self):
        response = self.client.post(self.endpoint, {
            'registration_number': 'KA-01-AB-1234',
            'vehicle_type': 'Compact',
            'is_admin': True,
        }, format='json')
        self._assert_validation_error(response, 'non_field_errors')
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_non_string_client_fields_return_400_instead_of_coercion(self):
        for field, value in (
            ('registration_number', 12345),
            ('vehicle_type', 1),
            ('owner_name', 123),
            ('owner_phone', True),
        ):
            with self.subTest(field=field):
                response = self.client.post(self.endpoint, {
                    'registration_number': 'KA-01-AB-1234',
                    'vehicle_type': 'Compact',
                    field: value,
                }, format='json')
                self._assert_validation_error(response, field)
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_owner_fields_enforce_model_length_limits(self):
        for field, value in (
            ('owner_name', 'N' * 101),
            ('owner_phone', '9' * 21),
        ):
            with self.subTest(field=field):
                response = self.client.post(self.endpoint, {
                    'registration_number': 'KA-01-AB-1234',
                    'vehicle_type': 'Compact',
                    field: value,
                }, format='json')
                self._assert_validation_error(response, field)
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_profile_update_rejects_malformed_and_duplicate_plates_without_mutation(self):
        own_vehicle = Vehicle.objects.create(
            registration_number='KA-01-OWN-1234',
            vehicle_type='Compact',
            owner=self.owner,
        )
        Vehicle.objects.create(
            registration_number='KA-01-OTHER-1234',
            vehicle_type='SUV',
            owner=self.other_owner,
        )

        malformed = self.client.patch(
            f'{self.endpoint}{own_vehicle.pk}/',
            {'registration_number': 'KA/01/OWN/1234'},
            format='json',
        )
        self._assert_validation_error(malformed, 'registration_number')
        own_vehicle.refresh_from_db()
        self.assertEqual(own_vehicle.registration_number, 'KA-01-OWN-1234')

        duplicate = self.client.patch(
            f'{self.endpoint}{own_vehicle.pk}/',
            {'registration_number': 'KA-01-OTHER-1234'},
            format='json',
        )
        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(duplicate.data['code'], 'CONFLICT')
        own_vehicle.refresh_from_db()
        self.assertEqual(own_vehicle.registration_number, 'KA-01-OWN-1234')


from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature, skipUnless
from vehicles.serializers import VehicleSerializer


@skipUnless(connection.vendor == 'postgresql', 'Concurrent unique-conflict behavior is verified on PostgreSQL.')
class VehicleConcurrentRegistrationTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.users = [
            User.objects.create_user(
                username=f'us08_concurrent_{index}',
                email=f'us08-concurrent-{index}@parking.local',
                password='Password123!',
                role='Customer',
                status='active',
            )
            for index in range(2)
        ]
        self.tokens = []
        for user in self.users:
            token = AccessToken.for_user(user)
            token['token_version'] = user.token_version
            token['username'] = user.username
            token['role'] = user.role
            self.tokens.append(str(token))

    def test_concurrent_same_plate_creates_one_record_and_returns_one_conflict(self):
        # Force both requests to complete serializer validation (including the
        # preflight duplicate query) before either request reaches its INSERT.
        barrier = Barrier(2)
        original_validate = VehicleSerializer.validate

        def synchronized_validate(serializer, attrs):
            validated = original_validate(serializer, attrs)
            barrier.wait(timeout=15)
            return validated

        def submit(token):
            close_old_connections()
            try:
                client = APIClient()
                client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
                response = client.post(self.endpoint, {
                    'registration_number': 'KA-01-RACE-1234',
                    'vehicle_type': 'Compact',
                }, format='json')
                return response.status_code, response.data
            finally:
                close_old_connections()

        self.endpoint = '/api/v1/vehicles/'
        with patch.object(VehicleSerializer, 'validate', synchronized_validate):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(submit, token) for token in self.tokens]
                results = [future.result(timeout=25) for future in futures]

        self.assertEqual(sorted(status for status, _ in results), [201, 409])
        conflict_body = next(body for status, body in results if status == 409)
        self.assertEqual(conflict_body['code'], 'CONFLICT')
        self.assertEqual(
            Vehicle.objects.filter(registration_number='KA-01-RACE-1234').count(),
            1,
        )
