from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from parking_slots.models import ParkingSlot, ParkingZone
from vehicles.models import Vehicle

from .models import ParkingSession


class CheckInAPITests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.operator = User.objects.create_user(
            username="operator",
            password="test-password-123",
            role="Operator",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)

        self.zone = ParkingZone.objects.create(
            name="Zone A",
        )

        self.slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number="A-01",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )

        self.vehicle = Vehicle.objects.create(
            registration_number="KA-01-AB-1234",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
            owner=self.operator,
        )

        self.url = "/api/parking/check-in/"

    def check_in(self):
        return self.client.post(
            self.url,
            {"registration_number": self.vehicle.registration_number},
            format="json",
        )

    def test_successful_check_in_creates_session_and_occupies_slot(self):
        response = self.check_in()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["vehicle_registration"],
            self.vehicle.registration_number,
        )
        self.assertEqual(response.data["slot_id"], self.slot.pk)
        self.assertEqual(response.data["status"], "active")
        self.assertTrue(response.data["ticket_token"])

        self.slot.refresh_from_db()

        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.OCCUPIED,
        )
        self.assertEqual(ParkingSession.objects.count(), 1)

    def test_duplicate_active_check_in_returns_409(self):
        first_response = self.check_in()
        second_response = self.check_in()

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(ParkingSession.objects.count(), 1)

    def test_no_available_slots_returns_409(self):
        self.slot.status = ParkingSlot.Status.OCCUPIED
        self.slot.save(update_fields=["status"])

        response = self.check_in()

        self.assertEqual(response.status_code, 409)
        self.assertEqual(ParkingSession.objects.count(), 0)

    def test_incompatible_slot_returns_409(self):
        self.slot.vehicle_type = Vehicle.VEHICLE_TYPE_SUV
        self.slot.save(update_fields=["vehicle_type"])

        response = self.check_in()

        self.assertEqual(response.status_code, 409)
        self.assertEqual(ParkingSession.objects.count(), 0)

    def test_unknown_vehicle_returns_404(self):
        response = self.client.post(
            self.url,
            {"registration_number": "KA-99-XX-9999"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ParkingSession.objects.count(), 0)

    def test_customer_cannot_check_in(self):
        self.operator.role = "Customer"
        self.operator.save(update_fields=["role"])

        response = self.check_in()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ParkingSession.objects.count(), 0)

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.check_in()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(ParkingSession.objects.count(), 0)