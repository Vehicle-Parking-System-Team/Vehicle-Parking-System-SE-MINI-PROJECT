
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from operations.models import ParkingRecord
from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle


User = get_user_model()


class ParkingHistoryAPITests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user(
            username="history-operator",
            password="test-password-123",
            role="Operator",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)

        self.zone = ParkingZone.objects.create(name="History Zone")

        self.slot1 = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number="H-01",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )
        self.slot2 = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number="H-02",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )

        self.vehicle1 = Vehicle.objects.create(
            registration_number="KA-05-HI-1001",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
            owner=self.operator,
        )
        self.vehicle2 = Vehicle.objects.create(
            registration_number="KA-05-HI-1002",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
            owner=self.operator,
        )

        self.url = "/api/parking/history/"

    def create_completed_record(
        self,
        vehicle=None,
        slot=None,
        days_ago=0,
        fee_amount=Decimal("75.00"),
    ):
        vehicle = vehicle or self.vehicle1
        slot = slot or self.slot1

        record_date = timezone.localdate() - timedelta(days=days_ago)
        check_in = timezone.make_aware(
            datetime.combine(record_date, time(10, 0)),
            timezone.get_current_timezone(),
        )
        check_out = check_in + timedelta(hours=2)

        return ParkingRecord.objects.create(
            vehicle=vehicle,
            slot=slot,
            operator=self.operator,
            check_in_time=check_in,
            check_out_time=check_out,
            fee_amount=fee_amount,
            status=ParkingRecord.Status.COMPLETED,
        )

    def test_history_returns_completed_records_and_stored_fee(self):
        completed = self.create_completed_record()

        ParkingRecord.objects.create(
            vehicle=self.vehicle2,
            slot=self.slot2,
            operator=self.operator,
            status=ParkingRecord.Status.ACTIVE,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            completed.pk,
        )
        self.assertEqual(
            response.data["results"][0]["status"],
            ParkingRecord.Status.COMPLETED,
        )
        self.assertEqual(
            response.data["results"][0]["fee_amount"],
            "75.00",
        )

        completed.refresh_from_db()
        self.assertEqual(completed.fee_amount, Decimal("75.00"))

    def test_history_filters_by_registration_number(self):
        matching = self.create_completed_record(vehicle=self.vehicle1)
        self.create_completed_record(
            vehicle=self.vehicle2,
            slot=self.slot2,
        )

        response = self.client.get(
            self.url,
            {"registration_number": self.vehicle1.registration_number},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], matching.pk)

    def test_history_filters_by_vehicle_id(self):
        matching = self.create_completed_record(vehicle=self.vehicle2)

        response = self.client.get(
            self.url,
            {"vehicle_id": self.vehicle2.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], matching.pk)

    def test_history_filters_by_slot_id(self):
        matching = self.create_completed_record(slot=self.slot2)

        self.create_completed_record(
            vehicle=self.vehicle2,
            slot=self.slot1,
        )

        response = self.client.get(
            self.url,
            {"slot_id": self.slot2.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], matching.pk)

    def test_history_filters_by_inclusive_date_range(self):
        recent = self.create_completed_record(days_ago=1)
        self.create_completed_record(
            vehicle=self.vehicle2,
            slot=self.slot2,
            days_ago=10,
        )

        target_date = (
            timezone.localdate() - timedelta(days=1)
        ).isoformat()

        response = self.client.get(
            self.url,
            {
                "start_date": target_date,
                "end_date": target_date,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], recent.pk)

    def test_history_rejects_start_date_after_end_date(self):
        today = timezone.localdate()

        response = self.client.get(
            self.url,
            {
                "start_date": (today + timedelta(days=1)).isoformat(),
                "end_date": today.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_history_supports_pagination(self):
        self.create_completed_record(
            vehicle=self.vehicle1,
            days_ago=1,
        )
        self.create_completed_record(
            vehicle=self.vehicle2,
            slot=self.slot2,
            days_ago=2,
        )

        response = self.client.get(
            self.url,
            {"page": 1, "page_size": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_history_endpoint_does_not_allow_delete(self):
        record = self.create_completed_record()

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            ParkingRecord.objects.filter(pk=record.pk).exists()
        )

    def test_history_requires_authentication(self):
        self.create_completed_record()
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_customer_cannot_access_history(self):
        self.create_completed_record()

        self.operator.role = "Customer"
        self.operator.save(update_fields=["role"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
