"""US-29: real API producers, authorization, tampering and rollback regressions."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from billing.services import generate_receipt
from common.audit import record_audit_event
from common.models import AuditEvent
from operations.models import ParkingRecord
from operations.services import check_in_vehicle, check_out_vehicle
from parking_slots.models import ParkingSlot, ParkingZone
from rates.models import ParkingRate
from reservations.models import Reservation
from vehicles.models import Vehicle

User = get_user_model()
PASSWORD = 'AuditRegression-678!'
PEER_IP = '192.0.2.21'


class AuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='audit_admin', email='audit_admin@example.test',
            password=PASSWORD, role='Admin',
        )
        cls.operator = User.objects.create_user(
            username='audit_operator', email='audit_operator@example.test',
            password=PASSWORD, role='Operator',
        )
        cls.customer = User.objects.create_user(
            username='audit_customer', email='audit_customer@example.test',
            password=PASSWORD, role='Customer',
        )
        cls.zone = ParkingZone.objects.create(name='Audit Zone')
        cls.slot = ParkingSlot.objects.create(zone=cls.zone, slot_number='AUD-01')
        cls.vehicle = Vehicle.objects.create(
            owner=cls.customer, registration_number='KA01AB1234', vehicle_type='Compact',
        )
        cls.rate = ParkingRate.objects.create(vehicle_type='Compact', hourly_rate='40.00')

    def setUp(self):
        self.client = APIClient(REMOTE_ADDR=PEER_IP)

    def event(self, event_type):
        event = AuditEvent.objects.get(event_type=event_type)
        self.assertIsNotNone(event.occurred_at)
        self.assertEqual(event.ip_address, PEER_IP)
        return event

    def login(self):
        response = self.client.post('/api/auth/login/', {
            'username': self.customer.username, 'password': PASSWORD,
        }, format='json', HTTP_X_FORWARDED_FOR='198.51.100.99')
        self.assertEqual(response.status_code, 200)
        return response.data

    def completed_receipt(self):
        record = check_in_vehicle(self.vehicle.registration_number, self.operator, self.slot.pk)
        with patch('operations.services.timezone.now', return_value=record.check_in_time + timedelta(hours=2)):
            record = check_out_vehicle(self.vehicle.registration_number, self.operator)
        return generate_receipt(record)[0]

    def reservation(self):
        start = timezone.now() + timedelta(days=2)
        return Reservation.objects.create(
            customer=self.customer, vehicle=self.vehicle, slot=self.slot,
            start_time=start, end_time=start + timedelta(hours=1),
        )

    def test_admin_reads_stable_newest_first_order_and_filters(self):
        when = timezone.now()
        first = AuditEvent.objects.create(event_type='auth.logout', occurred_at=when, actor_id='17')
        second = AuditEvent.objects.create(event_type='auth.login_failed', occurred_at=when)
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/audit/', {'page_size': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], second.pk)
        self.assertIsNotNone(response.data['next'])
        response = self.client.get('/api/audit/', {'event_type': 'auth.logout', 'actor_id': '17'})
        self.assertEqual([item['id'] for item in response.data['results']], [first.pk])

    def test_pagination_cannot_return_more_than_100_rows(self):
        AuditEvent.objects.bulk_create([AuditEvent(event_type='auth.logout') for _ in range(105)])
        self.client.force_authenticate(self.admin)
        response = self.client.get('/api/audit/', {'page_size': 10000})
        self.assertEqual(len(response.data['results']), 100)
        self.assertEqual(response.data['count'], 105)

    def test_non_admins_cannot_read_or_write_and_role_spoofing_does_not_help(self):
        for user in (self.operator, self.customer):
            self.client.force_authenticate(user)
            for method in ('get', 'post', 'patch', 'put', 'delete'):
                with self.subTest(role=user.role, method=method):
                    response = getattr(self.client, method)(
                        '/api/audit/?role=Admin', HTTP_X_ROLE='Admin',
                    )
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(response.data['code'], 'PERMISSION_DENIED')

    def test_unauthenticated_request_is_401_and_inactive_admin_is_403(self):
        self.assertEqual(self.client.get('/api/audit/').status_code, 401)
        self.admin.status = 'suspended'
        self.admin.save(update_fields=['status'])
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get('/api/audit/').status_code, 403)

    def test_even_admin_cannot_modify_audit_events_through_api(self):
        self.client.force_authenticate(self.admin)
        for method in ('post', 'put', 'patch', 'delete'):
            self.assertEqual(getattr(self.client, method)('/api/audit/').status_code, 405)

    def test_instance_queryset_base_manager_and_bulk_tampering_are_rejected(self):
        event = record_audit_event('auth.logout', actor=self.admin)
        event.event_type = 'tampered'
        for mutation in (
            event.save, event.delete,
            lambda: AuditEvent.objects.filter(pk=event.pk).update(event_type='tampered'),
            lambda: AuditEvent.objects.filter(pk=event.pk).delete(),
            lambda: AuditEvent._base_manager.filter(pk=event.pk).update(event_type='tampered'),
            lambda: AuditEvent.objects.bulk_update([event], ['event_type']),
            lambda: AuditEvent.objects.bulk_create(
                [event], update_conflicts=True, update_fields=['event_type'], unique_fields=['id'],
            ),
        ):
            with self.subTest(mutation=mutation), self.assertRaises(TypeError):
                mutation()
        event.refresh_from_db()
        self.assertEqual(event.event_type, 'auth.logout')
        with self.assertRaises(TypeError):
            AuditEvent(pk=event.pk, event_type='tampered').save()

    def test_deleting_source_user_does_not_delete_or_rewrite_actor_snapshot(self):
        actor = User.objects.create_user(username='temporary_audited_actor', role='Admin')
        event = record_audit_event('auth.logout', actor=actor)
        actor_id = str(actor.pk)
        actor.delete()
        event.refresh_from_db()
        self.assertEqual((event.actor_id, event.actor_username), (actor_id, 'temporary_audited_actor'))

    def test_recorder_rejects_secret_fields_and_unknown_events(self):
        for event_type, details in (
            ('auth.logout', {'password': PASSWORD}),
            ('account.updated', {'new_state': {'access_token': 'secret'}}),
            ('invented.event', {}),
        ):
            with self.subTest(event=event_type), self.assertRaises(ValueError):
                record_audit_event(event_type, details=details)
        self.assertFalse(AuditEvent.objects.exists())

    def test_invalid_peer_address_is_omitted_and_proxy_header_is_ignored(self):
        request = RequestFactory().get('/', REMOTE_ADDR='invalid', HTTP_X_FORWARDED_FOR=PEER_IP)
        event = record_audit_event('auth.logout', request=request)
        self.assertIsNone(event.ip_address)

    def test_successful_login_has_actor_peer_ip_and_no_credentials_or_tokens(self):
        session = self.login()
        event = self.event('auth.login_succeeded')
        self.assertEqual(event.actor_id, str(self.customer.pk))
        self.assertEqual(event.actor_role, 'Customer')
        self.assertEqual(event.resource_id, str(self.customer.pk))
        self.assertEqual(event.details, {'outcome': 'success'})
        for secret in (PASSWORD, session['access'], session['refresh']):
            self.assertNotIn(secret, str(event.__dict__))

    def test_failed_login_is_durable_and_does_not_record_unverified_identity(self):
        for username in (self.customer.username, 'unknown_secret_identity'):
            response = self.client.post('/api/auth/login/', {
                'username': username, 'password': 'wrong-secret',
            }, format='json')
            self.assertEqual(response.status_code, 401)
        self.assertEqual(AuditEvent.objects.filter(event_type='auth.login_failed').count(), 2)
        for event in AuditEvent.objects.all():
            self.assertIsNone(event.actor_id)
            self.assertEqual(event.actor_username, '')
            self.assertEqual(event.details, {'outcome': 'failure'})
            self.assertEqual(event.ip_address, PEER_IP)

    def test_invalid_login_payload_does_not_create_success_event(self):
        self.assertEqual(self.client.post('/api/auth/login/', {}, format='json').status_code, 400)
        self.assertFalse(AuditEvent.objects.exists())

    def test_logout_records_event_and_revokes_access(self):
        session = self.login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {session['access']}")
        response = self.client.post('/api/auth/logout/', {'refresh': session['refresh']}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.event('auth.logout').actor_id, str(self.customer.pk))
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_login_audit_failure_rolls_back_token_creation(self):
        with patch('accounts.views.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.post('/api/auth/login/', {
                    'username': self.customer.username, 'password': PASSWORD,
                }, format='json')
        self.assertEqual(response.status_code, 500)
        self.assertFalse(OutstandingToken.objects.exists())

    def test_logout_audit_failure_rolls_back_revocation(self):
        session = self.login()
        original_version = self.customer.token_version
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {session['access']}")
        with patch('accounts.views.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.post('/api/auth/logout/', {'refresh': session['refresh']}, format='json')
        self.assertEqual(response.status_code, 500)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.token_version, original_version)
        self.assertFalse(BlacklistedToken.objects.exists())
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)

    def test_admin_role_and_status_change_has_before_and_after_and_noop_is_not_duplicated(self):
        self.client.force_authenticate(self.admin)
        url = f'/api/auth/users/{self.customer.pk}/'
        values = {'role': 'Operator', 'status': 'suspended'}
        self.assertEqual(self.client.patch(url, values, format='json').status_code, 200)
        event = self.event('account.updated')
        self.assertEqual(event.actor_id, str(self.admin.pk))
        self.assertEqual(event.details, {
            'previous_state': {'role': 'Customer', 'status': 'active'},
            'new_state': {'role': 'Operator', 'status': 'suspended'},
        })
        self.assertEqual(self.client.patch(url, values, format='json').status_code, 200)
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_role_change_audit_failure_rolls_back_user_update(self):
        self.client.force_authenticate(self.admin)
        with patch('accounts.views.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.patch(f'/api/auth/users/{self.customer.pk}/', {'role': 'Operator'}, format='json')
        self.assertEqual(response.status_code, 500)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, 'Customer')

    def test_denied_role_change_and_rejected_override_have_no_success_event(self):
        self.client.force_authenticate(self.customer)
        response = self.client.patch(f'/api/auth/users/{self.operator.pk}/', {'role': 'Admin'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.client.force_authenticate(self.operator)
        self.slot.status = ParkingSlot.Status.OCCUPIED
        self.slot.save(update_fields=['status'])
        response = self.client.patch(f'/api/parking/slots/{self.slot.pk}/status/', {'status': 'maintenance'}, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertFalse(AuditEvent.objects.exists())

    def test_slot_override_records_actor_and_before_after_states(self):
        self.client.force_authenticate(self.operator)
        response = self.client.patch(f'/api/parking/slots/{self.slot.pk}/status/', {'status': 'maintenance'}, format='json')
        self.assertEqual(response.status_code, 200)
        event = self.event('parking_slot.maintenance_changed')
        self.assertEqual(event.actor_id, str(self.operator.pk))
        self.assertEqual(event.details, {'previous_status': 'available', 'status': 'maintenance'})

    def test_slot_audit_failure_rolls_back_override(self):
        self.client.force_authenticate(self.operator)
        with patch('parking_slots.services.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.patch(f'/api/parking/slots/{self.slot.pk}/status/', {'status': 'maintenance'}, format='json')
        self.assertEqual(response.status_code, 500)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, ParkingSlot.Status.AVAILABLE)

    def test_zone_deactivation_methods_record_actor_resource_and_changed_slot_count(self):
        self.client.force_authenticate(self.admin)
        for method in ('patch', 'put', 'delete'):
            with self.subTest(method=method):
                zone = ParkingZone.objects.create(name=f'Audit {method}')
                ParkingSlot.objects.create(zone=zone, slot_number='01')
                ParkingSlot.objects.create(zone=zone, slot_number='02')
                ParkingSlot.objects.create(zone=zone, slot_number='03', is_active=False)
                response = getattr(self.client, method)(
                    f'/api/parking/zones/{zone.pk}/',
                    {'name': zone.name, 'is_active': False}, format='json',
                )
                self.assertEqual(response.status_code, 204 if method == 'delete' else 200)
                zone.refresh_from_db()
                self.assertFalse(zone.is_active)
                self.assertFalse(zone.slots.filter(is_active=True).exists())
                event = AuditEvent.objects.get(
                    event_type='parking_zone.deactivated', resource_id=str(zone.pk),
                )
                self.assertIsNotNone(event.occurred_at)
                self.assertEqual(event.ip_address, PEER_IP)
                self.assertEqual(event.actor_id, str(self.admin.pk))
                self.assertEqual(event.actor_username, self.admin.username)
                self.assertEqual(event.actor_role, 'Admin')
                self.assertEqual(event.resource_type, 'parking_zone')
                self.assertEqual(event.details, {
                    'previous_is_active': True, 'is_active': False, 'affected_slot_count': 2,
                })
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_active)
        self.assertEqual(AuditEvent.objects.count(), 3)

    def test_zone_audit_insert_failure_rolls_back_zone_and_all_child_changes(self):
        self.client.force_authenticate(self.admin)
        other = ParkingSlot.objects.create(zone=self.zone, slot_number='AUD-02')
        inactive = ParkingSlot.objects.create(zone=self.zone, slot_number='AUD-03', is_active=False)
        originals = {
            slot.pk: (slot.is_active, slot.updated_at)
            for slot in (self.slot, other, inactive)
        }
        original_updated_at = self.zone.updated_at
        for method in ('patch', 'put', 'delete'):
            with self.subTest(method=method):
                with patch('common.audit.AuditEvent.objects.create', side_effect=DatabaseError('audit unavailable')):
                    with self.assertLogs('common.exceptions', level='ERROR'):
                        response = getattr(self.client, method)(
                            f'/api/parking/zones/{self.zone.pk}/',
                            {'name': 'Must roll back', 'is_active': False}, format='json',
                        )
                self.assertEqual(response.status_code, 500)
                self.zone.refresh_from_db()
                self.assertTrue(self.zone.is_active)
                self.assertEqual(self.zone.name, 'Audit Zone')
                self.assertEqual(self.zone.updated_at, original_updated_at)
                for slot in (self.slot, other, inactive):
                    slot.refresh_from_db()
                    self.assertEqual((slot.is_active, slot.updated_at), originals[slot.pk])
                self.assertFalse(AuditEvent.objects.exists())

    def test_repeated_zone_deactivation_does_not_duplicate_event(self):
        self.client.force_authenticate(self.admin)
        for method in ('patch', 'put', 'delete'):
            response = getattr(self.client, method)(
                f'/api/parking/zones/{self.zone.pk}/',
                {'name': self.zone.name, 'is_active': False}, format='json',
            )
            self.assertEqual(response.status_code, 204 if method == 'delete' else 200)
        self.assertEqual(AuditEvent.objects.count(), 1)
        self.assertEqual(self.event('parking_zone.deactivated').details['affected_slot_count'], 1)

    def test_empty_zone_deactivation_is_still_audited(self):
        self.client.force_authenticate(self.admin)
        zone = ParkingZone.objects.create(name='Empty audited zone')
        self.assertEqual(self.client.delete(f'/api/parking/zones/{zone.pk}/').status_code, 204)
        self.assertEqual(self.event('parking_zone.deactivated').details, {
            'previous_is_active': True, 'is_active': False, 'affected_slot_count': 0,
        })

    def test_rejected_zone_deactivation_does_not_create_success_event(self):
        self.client.force_authenticate(self.admin)
        self.slot.status = ParkingSlot.Status.RESERVED
        self.slot.save(update_fields=['status'])
        for method in ('patch', 'put', 'delete'):
            response = getattr(self.client, method)(
                f'/api/parking/zones/{self.zone.pk}/',
                {'name': self.zone.name, 'is_active': False}, format='json',
            )
            self.assertEqual(response.status_code, 409)
        self.assertFalse(AuditEvent.objects.exists())

    def test_other_zone_updates_do_not_create_deactivation_event(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f'/api/parking/zones/{self.zone.pk}/',
            {'name': 'Renamed zone', 'is_active': True}, format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AuditEvent.objects.exists())

    def test_payment_and_waiver_events_and_idempotent_retries(self):
        for waived in (False, True):
            receipt = self.completed_receipt()
            self.client.force_authenticate(self.operator)
            url = f'/api/parking/receipts/{receipt.receipt_number}/payment/'
            values = {'payment_status': 'Waived' if waived else 'Paid', 'payment_amount': '0.00' if waived else str(receipt.fee_amount)}
            if not waived:
                values['payment_method'] = 'Cash'
            for _ in range(2):
                self.assertEqual(self.client.post(url, values, format='json').status_code, 200)
            event = self.event('billing.fee_waived' if waived else 'billing.payment_recorded')
            self.assertEqual(event.resource_id, str(receipt.pk))
            self.assertEqual(event.actor_id, str(self.operator.pk))
            self.assertEqual(event.details['payment_status'], values['payment_status'])
        self.assertEqual(AuditEvent.objects.count(), 2)

    def test_payment_audit_failure_rolls_back_receipt_and_session(self):
        receipt = self.completed_receipt()
        self.client.force_authenticate(self.operator)
        with patch('billing.services.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.post(f'/api/parking/receipts/{receipt.receipt_number}/payment/', {
                    'payment_status': 'Waived', 'payment_amount': '0.00',
                }, format='json')
        self.assertEqual(response.status_code, 500)
        receipt.refresh_from_db()
        self.assertEqual(receipt.payment_status, 'Pending')
        self.assertEqual(ParkingRecord.objects.get(pk=receipt.parking_record_id).payment_status, 'Pending')

    def test_tariff_change_including_penalty_is_audited_and_noop_is_omitted(self):
        self.client.force_authenticate(self.admin)
        url = f'/api/v1/rates/{self.rate.pk}/'
        for _ in range(2):
            self.assertEqual(self.client.patch(url, {'penalty_fee': '7.00'}, format='json').status_code, 200)
        event = self.event('tariff.updated')
        self.assertEqual(event.details['previous_state']['penalty_fee'], '0.00')
        self.assertEqual(event.details['new_state']['penalty_fee'], '7.00')

    def test_tariff_audit_failure_rolls_back_change(self):
        self.client.force_authenticate(self.admin)
        with patch('rates.views.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.patch(f'/api/v1/rates/{self.rate.pk}/', {'hourly_rate': '60.00'}, format='json')
        self.assertEqual(response.status_code, 500)
        self.rate.refresh_from_db()
        self.assertEqual(self.rate.hourly_rate, Decimal('40.00'))

    def test_reservation_cancellation_is_audited(self):
        reservation = self.reservation()
        self.client.force_authenticate(self.customer)
        response = self.client.delete(f'/api/parking/reservations/{reservation.pk}/')
        self.assertEqual(response.status_code, 200)
        event = self.event('reservation.cancelled')
        self.assertEqual(event.actor_id, str(self.customer.pk))
        self.assertEqual(event.details['status'], 'Cancelled')

    def test_cancellation_audit_failure_rolls_back_reservation(self):
        reservation = self.reservation()
        self.client.force_authenticate(self.customer)
        with patch('reservations.services.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.delete(f'/api/parking/reservations/{reservation.pk}/')
        self.assertEqual(response.status_code, 500)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, Reservation.Status.CONFIRMED)

    def test_outer_transaction_rollback_removes_event_with_its_operation(self):
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                record_audit_event('auth.logout', actor=self.customer)
                raise RuntimeError('outer operation failed')
        self.assertFalse(AuditEvent.objects.exists())

    def test_admin_account_creation_records_privileges_without_password_or_email(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/auth/users/', {
            'username': 'new_audited_operator', 'email': 'new_operator@example.test',
            'password': PASSWORD, 'role': 'Operator',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        event = self.event('account.created')
        self.assertEqual(event.actor_id, str(self.admin.pk))
        self.assertEqual(event.details, {'role': 'Operator', 'status': 'active'})
        self.assertNotIn(PASSWORD, str(event.__dict__))
        self.assertNotIn('new_operator@example.test', str(event.__dict__))

    def test_account_creation_audit_failure_rolls_back_new_account(self):
        self.client.force_authenticate(self.admin)
        with patch('accounts.views.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.post('/api/auth/users/', {
                    'username': 'rolled_back_operator', 'email': 'rollback@example.test',
                    'password': PASSWORD, 'role': 'Operator',
                }, format='json')
        self.assertEqual(response.status_code, 500)
        self.assertFalse(User.objects.filter(username='rolled_back_operator').exists())

    def test_password_change_records_only_event_metadata(self):
        self.client.force_authenticate(self.customer)
        new_password = 'ChangedAuditPassword-903!'
        response = self.client.post('/api/auth/password/change/', {
            'current_password': PASSWORD, 'new_password': new_password,
            'new_password_confirm': new_password,
        }, format='json')
        self.assertEqual(response.status_code, 200)
        event = self.event('auth.password_changed')
        self.assertEqual(event.details, {})
        self.assertNotIn(PASSWORD, str(event.__dict__))
        self.assertNotIn(new_password, str(event.__dict__))

    def test_password_audit_failure_rolls_back_password_and_token_version(self):
        self.client.force_authenticate(self.customer)
        original_version = self.customer.token_version
        with patch('accounts.views.record_audit_event', side_effect=DatabaseError('audit unavailable')):
            with self.assertLogs('common.exceptions', level='ERROR'):
                response = self.client.post('/api/auth/password/change/', {
                    'current_password': PASSWORD, 'new_password': 'ChangedAuditPassword-903!',
                }, format='json')
        self.assertEqual(response.status_code, 500)
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.check_password(PASSWORD))
        self.assertEqual(self.customer.token_version, original_version)

    def test_tariff_creation_has_audit_entry(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post('/api/v1/rates/', {
            'vehicle_type': 'SUV', 'hourly_rate': '90.00',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.event('tariff.created').details['new_state']['hourly_rate'], '90.00')

    def test_pending_payment_noop_does_not_create_settlement_event(self):
        receipt = self.completed_receipt()
        self.client.force_authenticate(self.operator)
        response = self.client.post(f'/api/parking/receipts/{receipt.receipt_number}/payment/', {
            'payment_status': 'Pending', 'payment_amount': '0.00',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AuditEvent.objects.exists())
