from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from .models import ParkingSlot, ParkingZone


ROOT = '/api/parking/'


class ParkingAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='manager', role='Admin')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.zone = ParkingZone.objects.create(name='Zone A')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number='A-01', floor=0, vehicle_type='Compact',
        )
        self.url = f'{ROOT}slots/{self.slot.pk}/'
        self.values = {'zone': self.zone.pk, 'slot_number': 'A-02', 'floor': -1, 'vehicle_type': 'SUV'}

    def test_create_defaults_available(self):
        response = self.client.post(f'{ROOT}slots/', self.values, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'available')
        self.assertEqual(response.data['zone_name'], 'Zone A')
        self.assertEqual(response.data['floor'], -1)

    def test_operator_can_manage(self):
        self.user.role = 'Operator'
        self.user.save()
        self.assertEqual(self.client.post(f'{ROOT}slots/', self.values).status_code, 201)

    def test_customer_cannot_read_or_write_management_api(self):
        self.user.role = 'Customer'
        self.user.save()
        for method, url, data in (
            ('get', f'{ROOT}slots/', {}), ('get', f'{ROOT}zones/', {}),
            ('post', f'{ROOT}slots/', self.values), ('post', f'{ROOT}zones/', {'name': 'New'}),
            ('patch', self.url, {'is_active': False}), ('delete', self.url, {}),
            ('patch', self.url + 'status/', {'status': 'maintenance'}),
        ):
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(self.client, method)(url, data, format='json').status_code, 403)

    def test_inactive_accounts_denied(self):
        for status, active in [('suspended', True), ('deactivated', True), ('active', False)]:
            self.user.status, self.user.is_active = status, active
            self.assertEqual(self.client.get(f'{ROOT}slots/').status_code, 403)

    def test_authentication_required(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f'{ROOT}slots/')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(set(response.data), {'error', 'code', 'details'})

    def test_floor_and_type_required_for_new_bays(self):
        for field in ('floor', 'vehicle_type'):
            values = {key: value for key, value in self.values.items() if key != field}
            response = self.client.post(f'{ROOT}slots/', values, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data['details'])

    def test_invalid_floor_and_type(self):
        for changes in ({'floor': None}, {'floor': 1.5}, {'vehicle_type': 'any'}, {'vehicle_type': 'VAN'}):
            self.assertEqual(self.client.post(f'{ROOT}slots/', {**self.values, **changes}, format='json').status_code, 400)

    def test_all_existing_vehicle_choices_supported(self):
        from vehicles.models import Vehicle
        for index, (value, _) in enumerate(Vehicle.VEHICLE_TYPE_CHOICES):
            response = self.client.post(f'{ROOT}slots/', {
                **self.values, 'slot_number': f'Type-{index}', 'vehicle_type': value,
            }, format='json')
            self.assertEqual(response.status_code, 201)

    def test_legacy_values_preserved_during_unrelated_edit(self):
        for value in ('any', 'VAN'):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(vehicle_type=value, floor=None)
            response = self.client.patch(self.url, {'slot_number': 'Legacy', 'vehicle_type': value}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['vehicle_type'], value)
            self.assertIsNone(response.data['floor'])

    def test_assign_real_floor_to_legacy_bay(self):
        ParkingSlot.objects.filter(pk=self.slot.pk).update(floor=None)
        self.assertEqual(self.client.patch(self.url, {'floor': 2}, format='json').data['floor'], 2)

    def test_unique_number_per_zone_retained(self):
        response = self.client.post(f'{ROOT}slots/', {**self.values, 'slot_number': self.slot.slot_number}, format='json')
        self.assertEqual(response.status_code, 400)
        other = ParkingZone.objects.create(name='Zone B')
        response = self.client.post(f'{ROOT}slots/', {
            **self.values, 'slot_number': self.slot.slot_number, 'zone': other.pk,
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_slot_number_accepts_pr64_thirty_character_limit(self):
        self.assertEqual(self.client.post(f'{ROOT}slots/', {**self.values, 'slot_number': 'X' * 30}).status_code, 201)

    def test_cannot_create_inactive_zone_slot(self):
        self.zone.is_active = False
        self.zone.save()
        self.assertIn(self.client.post(f'{ROOT}slots/', self.values).status_code, (400, 409))

    def test_status_cannot_be_spoofed_on_create_or_update(self):
        self.assertEqual(self.client.post(f'{ROOT}slots/', {**self.values, 'status': 'occupied'}).status_code, 400)
        self.assertEqual(self.client.patch(self.url, {'status': 'available'}, format='json').status_code, 400)

    def test_occupied_and_reserved_slot_protection_all_write_paths(self):
        for state in ('occupied', 'reserved'):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=state)
            for method, data in (
                ('delete', {}), ('patch', {'is_active': False}),
                ('patch', {'floor': 7}), ('put', {**self.values, 'is_active': False}),
            ):
                with self.subTest(state=state, method=method, data=data):
                    response = getattr(self.client, method)(self.url, data, format='json')
                    self.assertEqual(response.status_code, 409)
                    self.assertEqual(response.data['code'], 'CONFLICT')
            self.slot.refresh_from_db()
            self.assertTrue(self.slot.is_active)
            self.assertEqual(self.slot.status, state)
            self.assertEqual(self.slot.floor, 0)

    def test_delete_unoccupied_retains_record(self):
        for state in ('available', 'maintenance'):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=state, is_active=True)
            self.assertEqual(self.client.delete(self.url).status_code, 204)
            self.slot.refresh_from_db()
            self.assertFalse(self.slot.is_active)
            self.assertEqual(self.slot.status, state)
            self.assertEqual(self.slot.zone_id, self.zone.pk)

    def test_slot_can_be_reactivated(self):
        self.client.delete(self.url)
        response = self.client.patch(self.url, {'is_active': True}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['is_active'])

    def test_zone_delete_deactivates_children_and_retains_rows(self):
        self.assertEqual(self.client.delete(f'{ROOT}zones/{self.zone.pk}/').status_code, 204)
        self.slot.refresh_from_db()
        self.zone.refresh_from_db()
        self.assertFalse(self.zone.is_active)
        self.assertFalse(self.slot.is_active)
        self.assertEqual(ParkingSlot.objects.count(), 1)
        self.client.patch(f'{ROOT}zones/{self.zone.pk}/', {'is_active': True}, format='json')
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_active)

    def test_zone_deactivation_rejects_protected_children_without_partial_changes(self):
        other = ParkingSlot.objects.create(zone=self.zone, slot_number='Other')
        for state in ('occupied', 'reserved'):
            ParkingSlot.objects.filter(pk=self.slot.pk).update(status=state)
            for method in ('delete', 'patch', 'put'):
                response = getattr(self.client, method)(f'{ROOT}zones/{self.zone.pk}/', {
                    'name': self.zone.name, 'is_active': False,
                }, format='json')
                self.assertEqual(response.status_code, 409)
            other.refresh_from_db()
            self.zone.refresh_from_db()
            self.assertTrue(other.is_active)
            self.assertTrue(self.zone.is_active)

    def test_status_endpoint_only_manages_maintenance(self):
        status_url = self.url + 'status/'
        self.assertEqual(self.client.patch(status_url, {'status': 'maintenance'}, format='json').status_code, 200)
        self.assertEqual(self.client.patch(status_url, {'status': 'available'}, format='json').status_code, 200)
        for value in ('occupied', 'reserved', 'invalid'):
            self.assertEqual(self.client.patch(status_url, {'status': value}, format='json').status_code, 400)

    def test_occupied_cannot_be_released_through_maintenance(self):
        ParkingSlot.objects.filter(pk=self.slot.pk).update(status='occupied')
        self.assertEqual(self.client.patch(self.url + 'status/', {'status': 'available'}, format='json').status_code, 409)

    def test_list_and_filters_preserve_native_contract(self):
        response = self.client.get(f'{ROOT}slots/?zone={self.zone.pk}&status=available')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertIn('vehicle_type', response.data[0])
        self.assertNotIn('slot_type', response.data[0])
        self.assertEqual(self.client.get(f'{ROOT}zones/').status_code, 200)

    def test_bad_filters_return_validation_envelope(self):
        for query in ('zone=garbage', 'status=invalid'):
            response = self.client.get(f'{ROOT}slots/?{query}')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.data['code'], 'VALIDATION_ERROR')

    def test_admin_cannot_bypass_state_guards(self):
        request = RequestFactory().get('/admin/')
        request.user = self.user
        for model in (ParkingSlot, ParkingZone):
            model_admin = admin.site._registry[model]
            self.assertTrue(model_admin.has_view_permission(request))
            self.assertFalse(model_admin.has_add_permission(request))
            self.assertFalse(model_admin.has_change_permission(request))
            self.assertFalse(model_admin.has_delete_permission(request))
