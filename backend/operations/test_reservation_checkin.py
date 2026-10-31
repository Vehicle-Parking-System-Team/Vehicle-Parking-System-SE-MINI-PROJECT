from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from operations.models import ParkingRecord
from parking_slots.models import ParkingSlot, ParkingZone
from reservations.models import Reservation
from vehicles.models import Vehicle


User = get_user_model()


class ReservationCheckInTests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user(
            username="reservation-operator", password="test-password-123", role="Operator",
        )
        self.customer = User.objects.create_user(
            username="reservation-customer", password="test-password-123", role="Customer",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)
        self.zone = ParkingZone.objects.create(name="Reservation check-in zone")
        self.slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number="R-01", vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )
        self.other_slot = ParkingSlot.objects.create(
            zone=self.zone, slot_number="R-02", vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )
        self.vehicle = Vehicle.objects.create(
            registration_number="KA-01-AB-9001",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT, owner=self.customer,
        )
        now = timezone.now()
        self.reservation = Reservation.objects.create(
            customer=self.customer, vehicle=self.vehicle, slot=self.slot,
            start_time=now - timedelta(minutes=5),
            end_time=now + timedelta(minutes=55),
        )
        self.url = "/api/parking/check-in/"

    def check_in(self, code=None, **kwargs):
        payload = {"registration_number": self.vehicle.registration_number, **kwargs}
        if code is not None:
            payload["reservation_code"] = code
        return self.client.post(self.url, payload, format="json")

    def test_code_assigns_reserved_slot_and_fulfills_reservation(self):
        response = self.check_in(f"RES-{self.reservation.pk}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["slot_id"], self.slot.pk)
        self.assertEqual(response.data["reservation_id"], self.reservation.pk)
        self.reservation.refresh_from_db()
        self.slot.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.FULFILLED)
        self.assertEqual(self.slot.status, ParkingSlot.Status.OCCUPIED)
        self.assertEqual(ParkingRecord.objects.count(), 1)

    def test_invalid_code_does_not_create_walk_in(self):
        for code in ("invalid", "RES-999999"):
            with self.subTest(code=code):
                response = self.check_in(code)
                self.assertEqual(response.status_code, 400)
                self.assertIn("walk-in", str(response.data).lower())
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_expired_and_not_yet_started_codes_rejected(self):
        self.reservation.end_time = timezone.now() - timedelta(seconds=1)
        self.reservation.save(update_fields=["end_time"])
        self.assertEqual(self.check_in(f"RES-{self.reservation.pk}").status_code, 400)
        self.reservation.start_time = timezone.now() + timedelta(minutes=5)
        self.reservation.end_time = timezone.now() + timedelta(minutes=65)
        self.reservation.save(update_fields=["start_time", "end_time"])
        self.assertEqual(self.check_in(f"RES-{self.reservation.pk}").status_code, 400)
        self.assertFalse(ParkingRecord.objects.exists())

    def test_other_vehicle_code_is_rejected(self):
        other_vehicle = Vehicle.objects.create(
            registration_number="KA-01-AB-9002",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT, owner=self.customer,
        )
        response = self.client.post(self.url, {
            "registration_number": other_vehicle.registration_number,
            "reservation_code": f"RES-{self.reservation.pk}",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ParkingRecord.objects.exists())

    def test_manual_slot_override_rejected_with_code(self):
        response = self.check_in(f"RES-{self.reservation.pk}", slot_id=self.other_slot.pk)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ParkingRecord.objects.exists())

    def test_repeated_code_cannot_create_second_session(self):
        code = f"RES-{self.reservation.pk}"
        self.assertEqual(self.check_in(code).status_code, 201)
        self.assertEqual(self.check_in(code).status_code, 409)
        self.assertEqual(ParkingRecord.objects.count(), 1)

    def test_cancelled_reservation_rejected(self):
        self.reservation.status = Reservation.Status.CANCELLED
        self.reservation.save(update_fields=["status"])
        self.assertEqual(self.check_in(f"RES-{self.reservation.pk}").status_code, 400)
        self.assertFalse(ParkingRecord.objects.exists())

    def test_future_reservation_protects_slot_from_other_vehicle_walk_in(self):
        self.reservation.start_time = timezone.now() + timedelta(days=2)
        self.reservation.end_time = self.reservation.start_time + timedelta(hours=1)
        self.reservation.save(update_fields=["start_time", "end_time"])
        other_vehicle = Vehicle.objects.create(
            registration_number="KA-01-AB-9010",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT, owner=self.customer,
        )
        response = self.client.post(self.url, {
            "registration_number": other_vehicle.registration_number,
            "slot_id": self.slot.pk,
        }, format="json")
        self.assertEqual(response.status_code, 409)
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.status, ParkingSlot.Status.AVAILABLE)
        self.assertFalse(ParkingRecord.objects.filter(vehicle=other_vehicle).exists())

        # Automatic walk-in allocation must also skip the reserved slot.
        response = self.client.post(self.url, {
            "registration_number": other_vehicle.registration_number,
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["slot_id"], self.other_slot.pk)
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, Reservation.Status.CONFIRMED)

    def test_reservation_create_and_detail_return_same_code(self):
        start = timezone.now() + timedelta(days=3)
        response = self.client.post("/api/parking/reservations/", {
            "vehicle": self.vehicle.pk,
            "slot": self.other_slot.pk,
            "start_time": start.isoformat(),
            "duration_minutes": 60,
        }, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        reservation_id = response.data["id"]
        self.assertEqual(response.data["reservation_code"], f"RES-{reservation_id}")
        detail = self.client.patch(
            f"/api/parking/reservations/{reservation_id}/", {
                "start_time": (start + timedelta(hours=1)).isoformat(),
                "duration_minutes": 60,
            }, format="json",
        )
        self.assertEqual(detail.status_code, 200, detail.data)
        self.assertEqual(detail.data["reservation_code"], f"RES-{reservation_id}")
