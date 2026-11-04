from datetime import timedelta
from unittest.mock import patch

from django.db import DatabaseError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from operations.models import ParkingRecord
from operations.services import check_in_vehicle, check_out_vehicle
from parking_slots.models import ParkingSlot, ParkingZone
from rates.models import ParkingRate
from reservations.models import Reservation
from vehicles.models import Vehicle
from .models import Notification
from .services import notify_expiring_reservations, schedule_parking_notification


class NotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username='notifications-admin', role='Admin')
        cls.operator = User.objects.create_user(username='notifications-operator', role='Operator')
        cls.owner = User.objects.create_user(username='notifications-owner', role='Customer')
        cls.other = User.objects.create_user(username='notifications-other', role='Customer')
        cls.zone = ParkingZone.objects.create(name='Notifications zone')
        cls.slot = ParkingSlot.objects.create(zone=cls.zone, slot_number='N1')
        cls.vehicle = Vehicle.objects.create(owner=cls.owner, registration_number='KA01AB1234', vehicle_type='Compact')
        ParkingRate.objects.create(vehicle_type='Compact', hourly_rate='20.00')

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def check_in(self):
        with self.captureOnCommitCallbacks(execute=True):
            return check_in_vehicle(self.vehicle.registration_number, self.operator)

    def checkout(self):
        with self.captureOnCommitCallbacks(execute=True):
            return check_out_vehicle(self.vehicle.registration_number, self.operator)

    def reservation(self, **kwargs):
        now = timezone.now()
        return Reservation.objects.create(customer=self.owner, vehicle=self.vehicle, slot=self.slot,
                                          start_time=now-timedelta(minutes=30),
                                          end_time=kwargs.pop('end_time', now+timedelta(minutes=10)), **kwargs)

    def test_capacity_alert_only_reaches_active_staff_after_commit(self):
        User.objects.create_user(username='suspended-staff', role='Operator', status='suspended')
        User.objects.create_user(username='inactive-staff', role='Admin', is_active=False)
        ParkingSlot.objects.create(zone=self.zone, slot_number='Inactive', is_active=False)
        with self.captureOnCommitCallbacks(execute=True):
            record = check_in_vehicle(self.vehicle.registration_number, self.operator)
            self.assertFalse(Notification.objects.exists())
        self.assertEqual(set(Notification.objects.values_list('recipient_id', flat=True)), {self.admin.pk, self.operator.pk})
        self.assertEqual(Notification.objects.first().kind, 'facility_full')
        with self.captureOnCommitCallbacks(execute=True):
            schedule_parking_notification('facility_full', record.pk)
        self.assertEqual(Notification.objects.count(), 2)

    def test_remaining_available_space_does_not_trigger_full_alert(self):
        ParkingSlot.objects.create(zone=self.zone, slot_number='N2')
        self.check_in()
        self.assertFalse(Notification.objects.exists())

    def test_checkout_confirms_owner_once_without_claiming_payment(self):
        record = self.check_in()
        self.checkout()
        with self.captureOnCommitCallbacks(execute=True):
            schedule_parking_notification('checkout', record.pk)
        alert = Notification.objects.get(recipient=self.owner)
        self.assertEqual(alert.kind, 'checkout')
        self.assertIn(self.vehicle.registration_number, alert.message)
        self.assertFalse(Notification.objects.filter(recipient=self.other).exists())
        self.assertEqual(Notification.objects.filter(kind='checkout').count(), 1)

    def test_full_alert_can_trigger_again_after_release_and_refill(self):
        self.check_in()
        self.checkout()
        self.check_in()
        self.assertEqual(Notification.objects.filter(recipient=self.operator, kind='facility_full').count(), 2)

    def test_rolled_back_checkin_emits_nothing(self):
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    check_in_vehicle(self.vehicle.registration_number, self.operator)
                    raise RuntimeError('rollback')
            except RuntimeError:
                pass
        self.assertFalse(ParkingRecord.objects.exists())
        self.assertFalse(Notification.objects.exists())

    def test_receipt_failure_rolls_back_checkout_and_alert(self):
        record = self.check_in()
        self.client.force_authenticate(self.operator)
        with self.captureOnCommitCallbacks(execute=True), patch('operations.views.generate_receipt', side_effect=RuntimeError('failure')):
            self.client.raise_request_exception = False
            response = self.client.post('/api/parking/check-out/', {'registration_number': self.vehicle.registration_number})
        self.assertEqual(response.status_code, 500)
        record.refresh_from_db()
        self.assertEqual(record.status, ParkingRecord.Status.ACTIVE)
        self.assertFalse(Notification.objects.filter(kind='checkout').exists())

    def test_dispatch_database_failure_does_not_block_parking(self):
        with patch('notifications.services.Notification.objects.bulk_create', side_effect=DatabaseError('unavailable')):
            self.check_in()
            record = self.checkout()
        record.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(record.status, ParkingRecord.Status.COMPLETED)
        self.assertEqual(self.slot.status, ParkingSlot.Status.AVAILABLE)
        self.assertFalse(Notification.objects.exists())

    def test_real_checkout_api_succeeds_when_notification_dispatch_fails(self):
        self.check_in()
        self.client.force_authenticate(self.operator)
        with self.captureOnCommitCallbacks(execute=True), patch('notifications.services._parking_event', side_effect=RuntimeError('failure')):
            response = self.client.post('/api/parking/check-out/', {'registration_number': self.vehicle.registration_number})
        self.assertEqual(response.status_code, 200)
        self.assertIn('receipt', response.json())

    def test_expiry_window_ownership_and_dismissed_event_deduplication(self):
        now = timezone.now()
        with patch('notifications.services.timezone.now', return_value=now):
            self.reservation(end_time=now+timedelta(minutes=15))
            self.reservation(end_time=now)
            self.reservation(end_time=now+timedelta(minutes=16))
            self.reservation(status=Reservation.Status.CANCELLED)
            self.reservation(status=Reservation.Status.FULFILLED)
            notify_expiring_reservations(self.other)
            self.assertFalse(Notification.objects.exists())
            response = self.client.get('/api/notifications/')
            self.assertEqual(response.json()['unread_count'], 1)
            alert = Notification.objects.get()
            self.client.post(f'/api/notifications/{alert.pk}/read/')
            response = self.client.get('/api/notifications/')
            self.assertEqual(response.json()['unread_count'], 0)
            self.assertEqual(Notification.objects.count(), 1)

    def test_inbox_read_is_owned_idempotent_and_not_implicit_on_view(self):
        alert = Notification.objects.create(recipient=self.owner, kind='checkout', event_key='owned', message='Done')
        Notification.objects.create(recipient=self.other, kind='checkout', event_key='other', message='Private')
        response = self.client.get('/api/notifications/?unread_only=true')
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['unread_count'], 1)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIsNone(response.json()['results'][0]['read_at'])
        first = self.client.post(f'/api/notifications/{alert.pk}/read/').json()
        second = self.client.post(f'/api/notifications/{alert.pk}/read/').json()
        self.assertEqual(first, second)
        self.assertEqual(first['unread_count'], 0)
        self.assertEqual(self.client.get('/api/notifications/?unread_only=true').json()['results'], [])
        self.assertEqual(self.client.get('/api/notifications/').json()['count'], 1)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(f'/api/notifications/{alert.pk}/read/').status_code, 404)
        self.assertEqual(self.client.post('/api/notifications/9999/read/').status_code, 404)

    def test_pagination_query_validation_and_read_only_list(self):
        Notification.objects.bulk_create([Notification(recipient=self.owner, kind='checkout', event_key=str(i), message='Done') for i in range(25)])
        response = self.client.get('/api/notifications/').json()
        self.assertEqual(len(response['results']), 20)
        self.assertEqual(response['unread_count'], 25)
        self.assertIsNotNone(response['next'])
        self.assertEqual(len(self.client.get('/api/notifications/?page=2').json()['results']), 5)
        self.assertEqual(self.client.get('/api/notifications/?unread_only=invalid').status_code, 400)
        self.assertEqual(self.client.post('/api/notifications/').status_code, 405)

    def test_jwt_and_account_status_authorization(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/notifications/').status_code, 401)
        token = AccessToken.for_user(self.owner)
        token['token_version'] = self.owner.token_version
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(self.client.get('/api/notifications/').status_code, 200)
        self.owner.status = 'suspended'
        self.owner.save(update_fields=['status'])
        self.assertEqual(self.client.get('/api/notifications/').status_code, 401)
