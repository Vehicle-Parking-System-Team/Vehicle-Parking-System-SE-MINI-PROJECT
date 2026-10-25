import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.signing import Signer
from django.db import close_old_connections, connections
from django.db import IntegrityError
from django.test import (
    TestCase,
    TransactionTestCase,
    skipUnlessDBFeature,
)
from rest_framework.test import APIClient

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot, ParkingZone
from parking_slots.services import occupy_slot as real_occupy_slot
from vehicles.models import Vehicle

from .models import ParkingRecord
from .services import check_in_vehicle, TICKET_SIGNING_SALT


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

        self.zone = ParkingZone.objects.create(
            name="Zone A",
        )

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

        self.url = "/api/parking/check-in/"

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
        self.assertEqual(response.data['code'], 'VALIDATION_ERROR')
        self.assertIn('slot_id', response.data['details'])
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

        self.assertEqual(
            ParkingRecord.objects.filter(
                vehicle=self.vehicle,
                status=ParkingRecord.Status.ACTIVE,
            ).count(),
            1,
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
        original_slot_id = self.slot.pk

        def change_type_before_occupation(slot_id):
            if slot_id == original_slot_id:
                ParkingSlot.objects.filter(
                    pk=slot_id,
                ).update(
                    vehicle_type=Vehicle.VEHICLE_TYPE_SUV,
                )

            return real_occupy_slot(slot_id)

        with patch(
            "operations.services.occupy_slot",
            side_effect=change_type_before_occupation,
        ):
            response = self.check_in()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["slot_id"],
            self.second_slot.pk,
        )

        self.slot.refresh_from_db()
        self.second_slot.refresh_from_db()

        # The failed candidate's transaction must be rolled back.
        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.AVAILABLE,
        )
        self.assertEqual(
            self.slot.vehicle_type,
            Vehicle.VEHICLE_TYPE_COMPACT,
        )

        # Automatic allocation should continue to the second slot.
        self.assertEqual(
            self.second_slot.status,
            ParkingSlot.Status.OCCUPIED,
        )

    def test_manual_selection_rechecks_compatibility_after_lock(self):
        original_slot_id = self.slot.pk

        def change_type_before_occupation(slot_id):
            if slot_id == original_slot_id:
                ParkingSlot.objects.filter(
                    pk=slot_id,
                ).update(
                    vehicle_type=Vehicle.VEHICLE_TYPE_SUV,
                )

            return real_occupy_slot(slot_id)

        with patch(
            "operations.services.occupy_slot",
            side_effect=change_type_before_occupation,
        ):
            response = self.check_in(slot_id=self.slot.pk)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(ParkingRecord.objects.count(), 0)

        self.slot.refresh_from_db()

        # Failed manual allocation must not leave a slot occupied
        # or retain the simulated compatibility change.
        self.assertEqual(
            self.slot.status,
            ParkingSlot.Status.AVAILABLE,
        )
        self.assertEqual(
            self.slot.vehicle_type,
            Vehicle.VEHICLE_TYPE_COMPACT,
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

        self.zone = ParkingZone.objects.create(
            name="Concurrency Zone",
        )

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
