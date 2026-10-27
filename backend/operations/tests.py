import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.signing import Signer
from django.db import IntegrityError, close_old_connections, connections
from django.test import (
    TestCase,
    TransactionTestCase,
    skipUnlessDBFeature,
)
from django.utils import timezone
from rest_framework.test import APIClient

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot, ParkingZone
from parking_slots.services import occupy_slot as real_occupy_slot
from vehicles.models import Vehicle
from rates.models import ParkingRate

from .models import ParkingRecord
from .services import TICKET_SIGNING_SALT, check_in_vehicle


User = get_user_model()


class CheckInAPITests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user(
            username="operator",
            password="test-password-123",
            role="Operator",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.operator)

        self.zone = ParkingZone.objects.create(name="Zone A")

        self.slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number="A-01",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )

        self.second_slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number="A-02",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )

        self.vehicle = Vehicle.objects.create(
            registration_number="KA-01-AB-1234",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
            owner=self.operator,
        )

        # Checkout now processes the configured tariff before releasing the slot.
        ParkingRate.objects.create(
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT, hourly_rate="40.00",
        )

        self.url = "/api/parking/check-in/"
        self.checkout_url = "/api/parking/check-out/"

    def check_in(self, **overrides):
        payload = {
            "registration_number": self.vehicle.registration_number,
        }
        payload.update(overrides)

        return self.client.post(
            self.url,
            payload,
            format="json",
        )

    def check_out(self, **overrides):
        payload = {
            "registration_number": self.vehicle.registration_number,
        }
        payload.update(overrides)

        return self.client.post(
            self.checkout_url,
            payload,
            format="json",
        )

    def test_successful_check_in_records_operator(self):
        response = self.check_in(slot_id=self.slot.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["operator_id"], self.operator.pk)
        self.assertEqual(response.data["vehicle_id"], self.vehicle.pk)
        self.assertEqual(response.data["slot_id"], self.slot.pk)
        self.assertEqual(response.data["status"], "ACTIVE")

        record = ParkingRecord.objects.get(pk=response.data["id"])

        self.assertEqual(record.operator, self.operator)
        self.assertIsNotNone(record.check_in_time)
        self.assertIsNone(record.check_out_time)
        self.assertIsNone(response.data["duration_seconds"])

        self.slot.refresh_from_db()

        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.OCCUPIED,
        )

    def test_manual_slot_override_is_respected(self):
        response = self.check_in(slot_id=self.second_slot.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["slot_id"], self.second_slot.pk)

        self.slot.refresh_from_db()
        self.second_slot.refresh_from_db()

        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.AVAILABLE,
        )
        self.assertEqual(
            self.second_slot.status,
            ParkingSlot.Status.OCCUPIED,
        )

    def test_incompatible_manual_slot_is_rejected(self):
        incompatible_slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number="A-03",
            vehicle_type=Vehicle.VEHICLE_TYPE_SUV,
        )

        response = self.check_in(slot_id=incompatible_slot.pk)

        self.assertEqual(response.status_code, 422)

        self.assertFalse(
            ParkingRecord.objects.filter(
                vehicle=self.vehicle,
                status=ParkingRecord.Status.ACTIVE,
            ).exists()
        )

        incompatible_slot.refresh_from_db()

        self.assertEqual(
            incompatible_slot.status,
            ParkingSlot.Status.AVAILABLE,
        )

    def test_inactive_manual_slot_is_rejected(self):
        self.slot.is_active = False
        self.slot.save(update_fields=["is_active"])

        response = self.check_in(slot_id=self.slot.pk)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_duplicate_active_check_in_returns_409(self):
        first_response = self.check_in()
        second_response = self.check_in()

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 409)

        # US-18: Verify the standardized conflict response.
        self.assertEqual(
            second_response.data["code"],
            "CONFLICT",
        )

        existing_record = ParkingRecord.objects.get(
            vehicle=self.vehicle,
            status=ParkingRecord.Status.ACTIVE,
        )

        details = second_response.data["details"]

        self.assertEqual(
            details["existing_slot_id"],
            existing_record.slot_id,
        )
        self.assertEqual(
            details["existing_slot_number"],
            existing_record.slot.slot_number,
        )
        self.assertEqual(
            details["check_in_time"],
            existing_record.check_in_time.isoformat(),
        )

        # Only one active record may exist for this vehicle.
        self.assertEqual(
            ParkingRecord.objects.filter(
                vehicle=self.vehicle,
                status=ParkingRecord.Status.ACTIVE,
            ).count(),
            1,
        )

    def test_completed_session_allows_reentry(self):
        first_response = self.check_in()

        self.assertEqual(first_response.status_code, 201)

        previous_record = ParkingRecord.objects.get(
            pk=first_response.data["id"]
        )
        previous_slot = previous_record.slot

        # Simulate checkout completing the previous parking session.
        previous_record.status = ParkingRecord.Status.COMPLETED
        previous_record.check_out_time = timezone.now()
        previous_record.save(
            update_fields=["status", "check_out_time"],
        )

        # Simulate checkout releasing the parking slot.
        previous_slot.status = ParkingSlot.Status.AVAILABLE
        previous_slot.save(update_fields=["status"])

        # US-18: A completed session must not block a new check-in.
        second_response = self.check_in()

        self.assertEqual(second_response.status_code, 201)
        self.assertNotEqual(
            second_response.data["id"],
            first_response.data["id"],
        )
        self.assertEqual(
            second_response.data["status"],
            ParkingRecord.Status.ACTIVE,
        )

        self.assertEqual(
            ParkingRecord.objects.filter(
                vehicle=self.vehicle,
                status=ParkingRecord.Status.ACTIVE,
            ).count(),
            1,
        )

        self.assertEqual(
            ParkingRecord.objects.filter(
                vehicle=self.vehicle,
            ).count(),
            2,
        )

    def test_no_compatible_available_slot_returns_409(self):
        self.slot.status = ParkingSlot.Status.OCCUPIED
        self.slot.save(update_fields=["status"])

        self.second_slot.status = ParkingSlot.Status.MAINTENANCE
        self.second_slot.save(update_fields=["status"])

        response = self.check_in()

        self.assertEqual(response.status_code, 409)
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_unknown_vehicle_returns_404(self):
        response = self.client.post(
            self.url,
            {"registration_number": "KA-99-XX-9999"},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_customer_cannot_check_in(self):
        self.operator.role = "Customer"
        self.operator.save(update_fields=["role"])

        response = self.check_in()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.check_in()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_ticket_contains_signed_canonical_payload(self):
        response = self.check_in()

        self.assertEqual(response.status_code, 201)

        record = ParkingRecord.objects.get(pk=response.data["id"])
        payload = json.loads(record.ticket_qr_token)

        self.assertEqual(
            set(payload),
            {
                "sessionId",
                "vehiclePlate",
                "slotNumber",
                "checkInTime",
                "signature",
            },
        )

        self.assertEqual(payload["sessionId"], record.pk)
        self.assertEqual(
            payload["vehiclePlate"],
            record.vehicle.registration_number,
        )
        self.assertEqual(
            payload["slotNumber"],
            record.slot.slot_number,
        )
        self.assertEqual(
            payload["checkInTime"],
            record.check_in_time.isoformat(),
        )

        signature = payload.pop("signature")

        canonical_payload = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        expected_signature = Signer(
            salt=TICKET_SIGNING_SALT,
        ).signature(canonical_payload)

        self.assertEqual(signature, expected_signature)

    def test_session_creation_failure_rolls_back_slot_occupation(self):
        with patch(
            "operations.services.ParkingRecord.objects.create",
            side_effect=IntegrityError(
                "Simulated record creation failure"
            ),
        ):
            with self.assertRaises(IntegrityError):
                check_in_vehicle(
                    registration_number=self.vehicle.registration_number,
                    operator=self.operator,
                    slot_id=self.slot.pk,
                )

        self.slot.refresh_from_db()

        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.AVAILABLE,
        )
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_automatic_allocation_rechecks_compatibility_after_lock(self):
        def change_type_then_occupy(slot_id):
            if slot_id == self.slot.pk:
                # Simulate a slot becoming incompatible during allocation.
                ParkingSlot.objects.filter(pk=slot_id).update(
                    vehicle_type=Vehicle.VEHICLE_TYPE_SUV,
                )

            return real_occupy_slot(slot_id)

        with patch(
            "operations.services.occupy_slot",
            side_effect=change_type_then_occupy,
        ):
            response = self.check_in()

        # Allocation should skip the incompatible candidate and try the next.
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["slot_id"],
            self.second_slot.pk,
        )

        self.slot.refresh_from_db()
        self.second_slot.refresh_from_db()

        # The failed candidate's nested transaction should roll back.
        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.AVAILABLE,
        )
        self.assertEqual(
            self.slot.vehicle_type,
            Vehicle.VEHICLE_TYPE_COMPACT,
        )
        self.assertEqual(
            self.second_slot.status,
            ParkingSlot.Status.OCCUPIED,
        )

    def test_manual_selection_rechecks_compatibility_after_lock(self):
        def change_type_then_occupy(slot_id):
            if slot_id == self.slot.pk:
                ParkingSlot.objects.filter(pk=slot_id).update(
                    vehicle_type=Vehicle.VEHICLE_TYPE_SUV,
                )

            return real_occupy_slot(slot_id)

        with patch(
            "operations.services.occupy_slot",
            side_effect=change_type_then_occupy,
        ):
            response = self.check_in(slot_id=self.slot.pk)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(ParkingRecord.objects.count(), 0)

        self.slot.refresh_from_db()

        # The failed manual selection must not leave the slot modified.
        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.AVAILABLE,
        )
        self.assertEqual(
            self.slot.vehicle_type,
            Vehicle.VEHICLE_TYPE_COMPACT,
        )

    def test_checkout_records_exit_time_duration_and_releases_slot(self):
        checkin_response = self.check_in(slot_id=self.slot.pk)
        self.assertEqual(checkin_response.status_code, 201)

        record = ParkingRecord.objects.get(pk=checkin_response.data["id"])

        # Give the session a known duration of 1 hour and 5 seconds.
        checkout_time = timezone.now()
        expected_duration_seconds = 3605

        record.check_in_time = checkout_time - timedelta(
            seconds=expected_duration_seconds,
        )
        record.save(update_fields=["check_in_time"])

        # Use a fixed checkout time so the duration assertion is deterministic.
        with patch(
            "operations.services.timezone.now",
            return_value=checkout_time,
        ):
            response = self.check_out()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"],
            ParkingRecord.Status.COMPLETED,
        )
        self.assertEqual(
            response.data["duration_seconds"],
            expected_duration_seconds,
        )

        record.refresh_from_db()
        self.slot.refresh_from_db()

        self.assertEqual(
            record.status,
            ParkingRecord.Status.COMPLETED,
        )
        self.assertEqual(record.check_out_time, checkout_time)
        self.assertEqual(
            int(
                (record.check_out_time - record.check_in_time).total_seconds()
            ),
            expected_duration_seconds,
        )
        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.AVAILABLE,
        )

    def test_checkout_without_active_session_returns_404(self):
        response = self.check_out()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_checkout_unknown_vehicle_returns_404(self):
        response = self.check_out(
            registration_number="KA-99-XX-9999",
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_repeated_checkout_returns_404(self):
        checkin_response = self.check_in()
        self.assertEqual(checkin_response.status_code, 201)

        first_checkout = self.check_out()
        self.assertEqual(first_checkout.status_code, 200)

        second_checkout = self.check_out()

        self.assertEqual(second_checkout.status_code, 404)

        self.assertEqual(
            ParkingRecord.objects.filter(
                vehicle=self.vehicle,
                status=ParkingRecord.Status.COMPLETED,
            ).count(),
            1,
        )

    def test_customer_cannot_check_out(self):
        checkin_response = self.check_in()
        self.assertEqual(checkin_response.status_code, 201)

        self.operator.role = "Customer"
        self.operator.save(update_fields=["role"])

        response = self.check_out()

        self.assertEqual(response.status_code, 403)

        record = ParkingRecord.objects.get(pk=checkin_response.data["id"])
        self.slot.refresh_from_db()

        self.assertEqual(record.status, ParkingRecord.Status.ACTIVE)
        self.assertIsNone(record.check_out_time)
        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.OCCUPIED,
        )

    def test_unauthenticated_checkout_is_rejected(self):
        checkin_response = self.check_in()
        self.assertEqual(checkin_response.status_code, 201)

        self.client.force_authenticate(user=None)

        response = self.check_out()

        self.assertEqual(response.status_code, 401)

        record = ParkingRecord.objects.get(pk=checkin_response.data["id"])
        self.slot.refresh_from_db()

        self.assertEqual(record.status, ParkingRecord.Status.ACTIVE)
        self.assertIsNone(record.check_out_time)
        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.OCCUPIED,
        )

    def test_checkout_release_failure_rolls_back_completion(self):
        checkin_response = self.check_in()
        self.assertEqual(checkin_response.status_code, 201)

        record_id = checkin_response.data["id"]

        with patch(
            "operations.services.release_slot",
            side_effect=Conflict("Simulated slot release failure."),
        ):
            response = self.check_out()

        self.assertEqual(response.status_code, 409)

        record = ParkingRecord.objects.get(pk=record_id)
        self.slot.refresh_from_db()

        # The outer checkout transaction must roll back both changes.
        self.assertEqual(record.status, ParkingRecord.Status.ACTIVE)
        self.assertIsNone(record.check_out_time)
        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.OCCUPIED,
        )


@skipUnlessDBFeature("has_select_for_update")
class CheckInConcurrencyTests(TransactionTestCase):
    """Concurrency tests for databases supporting row-level locking."""

    reset_sequences = True

    def setUp(self):
        self.operator = User.objects.create_user(
            username="concurrent-operator",
            password="test-password-123",
            role="Operator",
        )

        self.zone = ParkingZone.objects.create(name="Concurrency Zone")

        self.slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number="C-01",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )

        self.second_slot = ParkingSlot.objects.create(
            zone=self.zone,
            slot_number="C-02",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
        )

        self.vehicle1 = Vehicle.objects.create(
            registration_number="KA-02-AA-1001",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
            owner=self.operator,
        )

        self.vehicle2 = Vehicle.objects.create(
            registration_number="KA-02-AA-1002",
            vehicle_type=Vehicle.VEHICLE_TYPE_COMPACT,
            owner=self.operator,
        )

    def run_concurrent_check_in(self, plate, barrier):
        close_old_connections()

        try:
            barrier.wait(timeout=10)

            record = check_in_vehicle(
                registration_number=plate,
                operator=self.operator,
            )

            return ("success", record.pk)

        except Conflict:
            return ("conflict", None)

        finally:
            connections.close_all()

    def test_two_concurrent_check_ins_for_same_vehicle(self):
        barrier = Barrier(2)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    self.run_concurrent_check_in,
                    self.vehicle1.registration_number,
                    barrier,
                )
                for _ in range(2)
            ]

            results = [
                future.result(timeout=30)
                for future in futures
            ]

        self.assertEqual(
            [result[0] for result in results].count("success"),
            1,
        )

        self.assertEqual(
            ParkingRecord.objects.filter(
                vehicle=self.vehicle1,
                status=ParkingRecord.Status.ACTIVE,
            ).count(),
            1,
        )

    def test_two_vehicles_competing_for_one_slot(self):
        self.second_slot.status = ParkingSlot.Status.MAINTENANCE
        self.second_slot.save(update_fields=["status"])

        barrier = Barrier(2)

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    self.run_concurrent_check_in,
                    plate,
                    barrier,
                )
                for plate in (
                    self.vehicle1.registration_number,
                    self.vehicle2.registration_number,
                )
            ]

            results = [
                future.result(timeout=30)
                for future in futures
            ]

        self.assertEqual(
            [result[0] for result in results].count("success"),
            1,
        )

        self.assertEqual(
            ParkingRecord.objects.filter(
                status=ParkingRecord.Status.ACTIVE,
            ).count(),
            1,
        )
