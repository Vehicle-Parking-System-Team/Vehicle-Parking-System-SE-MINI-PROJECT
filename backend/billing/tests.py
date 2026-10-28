from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from billing.models import BillingReceipt
from billing.views import _can_access_receipt
from operations.models import ParkingRecord
from operations.services import check_in_vehicle, check_out_vehicle
from parking_slots.models import ParkingSlot, ParkingZone
from rates.models import ParkingRate
from vehicles.models import Vehicle


User = get_user_model()
RECEIPTS_URL = '/api/parking/receipts/'


class BillingReceiptAPITests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user(
            username='us23_operator',
            password='ReceiptTest-123!',
            role='Operator',
        )
        self.admin = User.objects.create_user(
            username='us23_admin',
            password='ReceiptTest-123!',
            role='Admin',
        )
        self.customer = User.objects.create_user(
            username='us23_customer',
            password='ReceiptTest-123!',
            role='Customer',
        )
        self.other_customer = User.objects.create_user(
            username='us23_other_customer',
            password='ReceiptTest-123!',
            role='Customer',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.customer)

        self.zone = ParkingZone.objects.create(name='Receipt Zone')
        self.slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number='R-01',
            floor=0,
            vehicle_type='Compact',
        )
        self.vehicle = Vehicle.objects.create(
            registration_number='KA23BC2345',
            vehicle_type='Compact',
            owner=self.customer,
        )
        self.rate = ParkingRate.objects.create(
            vehicle_type='Compact',
            hourly_rate=Decimal('40.00'),
            vehicle_multiplier=Decimal('2.00'),
            grace_period_minutes=15,
        )

        self.record = check_in_vehicle(
            self.vehicle.registration_number,
            self.operator,
            self.slot.pk,
        )
        self.exit_time = self.record.check_in_time + timedelta(
            hours=1, minutes=20,
        )
        with patch('operations.services.timezone.now', return_value=self.exit_time):
            self.record = check_out_vehicle(
                self.vehicle.registration_number,
                self.operator,
            )
        self.record.refresh_from_db()

    def generate(self, **payload):
        if not payload:
            payload = {'record_id': self.record.pk}
        return self.client.post(RECEIPTS_URL, payload, format='json')

    def test_checkout_api_generates_receipt_atomically(self):
        active = check_in_vehicle(
            self.vehicle.registration_number,
            self.operator,
            self.slot.pk,
        )
        self.client.force_authenticate(user=self.operator)
        exit_time = active.check_in_time + timedelta(hours=2)

        with patch('operations.services.timezone.now', return_value=exit_time):
            response = self.client.post(
                '/api/parking/check-out/',
                {'registration_number': self.vehicle.registration_number},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['receipt']['parking_record_id'], active.pk)
        self.assertEqual(response.data['receipt']['total_fee'], '160.00')
        self.assertTrue(response.data['receipt']['invoice_number'].startswith('INV-'))
        self.assertTrue(
            BillingReceipt.objects.filter(parking_record_id=active.pk).exists()
        )

    def test_generated_receipt_has_unique_invoice_and_itemized_snapshots(self):
        response = self.generate()

        self.assertEqual(response.status_code, 201)
        data = response.data
        self.assertTrue(data['invoice_number'].startswith('INV-'))
        self.assertEqual(len(data['invoice_number']), 36)
        self.assertEqual(data['registration_number'], 'KA23BC2345')
        self.assertEqual(data['vehicle_type'], 'Compact')
        self.assertEqual(data['slot_number'], 'R-01')
        self.assertEqual(data['zone_name'], 'Receipt Zone')
        self.assertEqual(data['duration_seconds'], 4800)
        self.assertEqual(data['billable_hours'], 2)
        self.assertEqual(data['hourly_rate'], '40.00')
        self.assertEqual(data['base_amount'], '80.00')
        self.assertEqual(data['vehicle_multiplier'], '2.00')
        self.assertEqual(data['multiplier_adjustment'], '80.00')
        self.assertEqual(data['total_fee'], '160.00')
        self.assertEqual(data['currency'], 'INR')
        self.assertTrue(data['check_in_time'])
        self.assertTrue(data['check_out_time'])
        self.assertTrue(data['print_url'])
        self.assertEqual(BillingReceipt.objects.count(), 1)

    def test_generating_twice_returns_same_receipt(self):
        first = self.generate()
        second = self.generate()

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data['receipt_id'], second.data['receipt_id'])
        self.assertEqual(first.data['invoice_number'], second.data['invoice_number'])
        self.assertEqual(BillingReceipt.objects.count(), 1)

    def test_receipt_data_is_retrievable_via_api(self):
        generated = self.generate()
        receipt_id = generated.data['receipt_id']

        response = self.client.get(f'{RECEIPTS_URL}{receipt_id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['receipt_id'], receipt_id)
        self.assertEqual(response.data['total_fee'], '160.00')

    def test_receipt_has_printable_html_view(self):
        generated = self.generate()
        receipt_id = generated.data['receipt_id']

        response = self.client.get(f'{RECEIPTS_URL}{receipt_id}/print/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
        self.assertContains(response, generated.data['invoice_number'])
        self.assertContains(response, 'KA23BC2345')
        self.assertContains(response, 'Itemized charges')
        self.assertContains(response, '160.00')
        self.assertContains(response, 'window.print()')

    def test_open_session_receipt_returns_http_400(self):
        active = check_in_vehicle(
            self.vehicle.registration_number,
            self.operator,
            self.slot.pk,
        )
        self.assertEqual(active.status, ParkingRecord.Status.ACTIVE)

        response = self.generate(record_id=active.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn('record_id', response.data['details'])
        self.assertEqual(BillingReceipt.objects.count(), 0)

    def test_customer_cannot_generate_receipt_for_another_customer(self):
        self.client.force_authenticate(user=self.other_customer)

        response = self.generate()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(BillingReceipt.objects.count(), 0)

    def test_operator_can_generate_receipt(self):
        self.client.force_authenticate(user=self.operator)

        response = self.generate()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(BillingReceipt.objects.count(), 1)

    def test_unauthenticated_generation_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.generate()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(BillingReceipt.objects.count(), 0)

    def test_invalid_payload_and_unknown_session_are_rejected(self):
        response = self.generate(unexpected='field')
        self.assertEqual(response.status_code, 400)

        response = self.generate(record_id=999999)
        self.assertEqual(response.status_code, 404)

        self.assertEqual(BillingReceipt.objects.count(), 0)

    def test_receipt_snapshot_is_unchanged_after_session_details_change(self):
        generated = self.generate()
        receipt_id = generated.data['receipt_id']
        receipt = BillingReceipt.objects.get(receipt_number=receipt_id)

        self.record.registration_number_snapshot = 'CHANGED-REGISTRATION'
        self.record.slot_number_snapshot = 'CHANGED-SLOT'
        self.record.fee_amount = Decimal('999.00')
        self.record.save(update_fields=[
            'registration_number_snapshot', 'slot_number_snapshot', 'fee_amount',
        ])

        response = self.client.get(f'{RECEIPTS_URL}{receipt_id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['registration_number'], 'KA23BC2345')
        self.assertEqual(response.data['slot_number'], 'R-01')
        self.assertEqual(response.data['total_fee'], '160.00')
        self.assertEqual(receipt.fee_amount, Decimal('160.00'))

    def test_missing_receipt_returns_404(self):
        response = self.client.get(f'{RECEIPTS_URL}{uuid4()}/')
        self.assertEqual(response.status_code, 404)

    def test_customer_cannot_retrieve_someone_elses_receipt(self):
        generated = self.generate()
        receipt_id = generated.data['receipt_id']
        self.client.force_authenticate(user=self.other_customer)

        response = self.client.get(f'{RECEIPTS_URL}{receipt_id}/')
        printable = self.client.get(f'{RECEIPTS_URL}{receipt_id}/print/')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(printable.status_code, 403)

    def test_invoice_number_handles_uuid_and_string_values(self):
        receipt_number = uuid4()
        receipt = BillingReceipt(receipt_number=receipt_number)
        expected = f'INV-{receipt_number.hex.upper()}'
        self.assertEqual(receipt.invoice_number, expected)

        receipt.receipt_number = str(receipt_number)
        self.assertEqual(receipt.invoice_number, expected)

    def test_receipt_access_denies_user_without_role_attribute(self):
        roleless_user = SimpleNamespace(
            is_authenticated=True,
            is_account_active=True,
            pk=self.customer.pk,
        )
        self.assertFalse(_can_access_receipt(roleless_user, self.record))

    def test_zero_fee_checkout_within_grace_period(self):
        active = check_in_vehicle(
            self.vehicle.registration_number,
            self.operator,
            self.slot.pk,
        )
        exit_time = active.check_in_time + timedelta(minutes=10)
        self.client.force_authenticate(user=self.operator)

        with patch('operations.services.timezone.now', return_value=exit_time):
            response = self.client.post(
                '/api/parking/check-out/',
                {'registration_number': self.vehicle.registration_number},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        receipt_data = response.data['receipt']
        self.assertEqual(receipt_data['total_fee'], '0.00')
        self.assertEqual(receipt_data['billable_hours'], 0)
        receipt = BillingReceipt.objects.get(parking_record_id=active.pk)
        self.assertEqual(receipt.fee_amount, Decimal('0.00'))
        self.assertEqual(receipt.billable_hours, 0)

    def test_admin_can_retrieve_customer_receipt(self):
        generated = self.generate()
        receipt_id = generated.data['receipt_id']
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f'{RECEIPTS_URL}{receipt_id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['receipt_id'], receipt_id)

    def test_suspended_customer_cannot_retrieve_receipt(self):
        generated = self.generate()
        receipt_id = generated.data['receipt_id']
        self.customer.status = 'suspended'
        self.customer.save(update_fields=['status'])
        self.customer.refresh_from_db()
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(f'{RECEIPTS_URL}{receipt_id}/')

        self.assertEqual(response.status_code, 403)

