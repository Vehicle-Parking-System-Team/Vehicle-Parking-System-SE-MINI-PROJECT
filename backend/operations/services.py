import json

from django.core.signing import Signer
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot
from parking_slots.services import occupy_slot, release_slot
from vehicles.models import Vehicle
from vehicles.services import normalize_registration_number

from .models import ParkingRecord


TICKET_SIGNING_SALT = "vehicle-parking.entry-ticket.v1"


class _SlotCompatibilityChanged(Exception):
    """Raised when a slot becomes incompatible during allocation."""


def _is_compatible_slot(slot, vehicle):
    """Check whether a parking slot supports the requested vehicle type."""
    slot_type = (slot.vehicle_type or "").strip().casefold()
    vehicle_type = (vehicle.vehicle_type or "").strip().casefold()
    return slot_type in {"any", vehicle_type}


def _raise_duplicate_active_record_conflict(vehicle):
    """Reject duplicate check-in with details of the existing active session."""
    existing_record = (
        ParkingRecord.objects.select_related("slot")
        .filter(
            vehicle=vehicle,
            status=ParkingRecord.Status.ACTIVE,
        )
        .order_by("-check_in_time", "-pk")
        .first()
    )

    if existing_record is None:
        return

    raise Conflict(
        "This vehicle already has an active parking record.",
        details={
            "existing_slot_id": existing_record.slot_id,
            "existing_slot_number": (
                existing_record.slot_number_snapshot
                or existing_record.slot.slot_number
            ),
            "check_in_time": existing_record.check_in_time.isoformat(),
        },
    ) from None


def create_signed_ticket(record):
    """Generate a signed QR-ready ticket payload."""
    payload = {
        "sessionId": record.pk,
        "vehiclePlate": (
            record.registration_number_snapshot
            or record.vehicle.registration_number
        ),
        "slotNumber": (
            record.slot_number_snapshot or record.slot.slot_number
        ),
        "checkInTime": record.check_in_time.isoformat(),
    }

    canonical_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    signer = Signer(salt=TICKET_SIGNING_SALT)
    payload["signature"] = signer.signature(canonical_payload)

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )


@transaction.atomic
def check_in_vehicle(registration_number, operator, slot_id=None):
    """Check in a registered vehicle and allocate a compatible parking slot."""
    if operator is None or not getattr(operator, "is_authenticated", False):
        raise ValidationError(
            {"operator": "An authenticated operator is required."}
        )

    plate = normalize_registration_number(registration_number)
    if not plate:
        raise ValidationError(
            {"registration_number": "A vehicle registration number is required."}
        )

    # Lock the vehicle row to serialize same-vehicle check-ins on databases
    # that support SELECT FOR UPDATE.
    vehicle = (
        Vehicle.objects.select_for_update()
        .filter(registration_number=plate)
        .first()
    )
    if vehicle is None:
        raise NotFound(
            "No registered vehicle was found with this registration number."
        )

    _raise_duplicate_active_record_conflict(vehicle)

    compatible_slots = ParkingSlot.objects.filter(
        Q(vehicle_type__iexact=vehicle.vehicle_type)
        | Q(vehicle_type__iexact="any")
    )

    if slot_id is not None:
        candidate = (
            ParkingSlot.objects.select_related("zone")
            .filter(pk=slot_id)
            .first()
        )
        if candidate is None:
            raise NotFound("The selected parking slot does not exist.")
        if not candidate.is_active or not candidate.zone.is_active:
            raise Conflict("The selected slot or its zone is inactive.")
        if candidate.status != ParkingSlot.Status.AVAILABLE:
            raise Conflict("The selected parking slot is not available.")
        if not _is_compatible_slot(candidate, vehicle):
            raise ValidationError(
                {"slot_id": "The selected slot is incompatible with this vehicle."}
            )
        candidate_ids = [candidate.pk]
    else:
        candidate_ids = list(
            compatible_slots.filter(
                status=ParkingSlot.Status.AVAILABLE,
                is_active=True,
                zone__is_active=True,
            )
            .order_by("zone__name", "slot_number", "pk")
            .values_list("pk", flat=True)
            .distinct()
        )

    for candidate_id in candidate_ids:
        try:
            with transaction.atomic():
                # Locks and updates the slot within the transaction.
                slot = occupy_slot(candidate_id)

                # Recheck compatibility after the slot lifecycle service has
                # locked and refreshed the slot.
                if not _is_compatible_slot(slot, vehicle):
                    raise _SlotCompatibilityChanged(
                        "The slot is no longer compatible."
                    )

                # Capture display details at check-in so later edits to the
                # vehicle, slot, or zone do not rewrite the historical record.
                record = ParkingRecord.objects.create(
                    vehicle=vehicle,
                    slot=slot,
                    operator=operator,
                    registration_number_snapshot=vehicle.registration_number,
                    vehicle_type_snapshot=vehicle.vehicle_type,
                    slot_number_snapshot=slot.slot_number,
                    zone_name_snapshot=slot.zone.name,
                    status=ParkingRecord.Status.ACTIVE,
                )

                # Generate the signed ticket after the database ID exists.
                # Keep token creation in the same transaction.
                record.ticket_qr_token = create_signed_ticket(record)
                record.save(update_fields=["ticket_qr_token"])

            return record

        except _SlotCompatibilityChanged:
            # The nested transaction rolls back the slot occupation.
            if slot_id is not None:
                raise ValidationError(
                    {
                        "slot_id": (
                            "The selected slot is no longer compatible with "
                            "this vehicle. Please choose another slot."
                        )
                    }
                ) from None
            # Automatic allocation can try another candidate.
            continue

        except Conflict:
            if slot_id is not None:
                raise
            continue

        except IntegrityError:
            # The inner transaction/savepoint has rolled back. Check whether
            # another request created an active record.
            _raise_duplicate_active_record_conflict(vehicle)
            if ParkingRecord.objects.filter(
                slot_id=candidate_id,
                status=ParkingRecord.Status.ACTIVE,
            ).exists():
                if slot_id is not None:
                    raise Conflict(
                        "The selected slot was allocated by another request."
                    ) from None
                continue
            # Do not hide unexpected integrity errors.
            raise

    raise Conflict(
        "Facility Full: no compatible parking slots are currently available."
    )


@transaction.atomic
def check_out_vehicle(registration_number, operator):
    """Complete the active parking session for a registered vehicle."""
    if operator is None or not getattr(operator, "is_authenticated", False):
        raise ValidationError(
            {"operator": "An authenticated operator is required."}
        )

    plate = normalize_registration_number(registration_number)
    if not plate:
        raise ValidationError(
            {"registration_number": "A vehicle registration number is required."}
        )

    # Lock the vehicle to serialize checkout and check-in operations on
    # databases supporting row-level locks.
    vehicle = (
        Vehicle.objects.select_for_update()
        .filter(registration_number=plate)
        .first()
    )
    if vehicle is None:
        raise NotFound(
            "No registered vehicle was found with this registration number."
        )

    record = (
        ParkingRecord.objects.select_for_update()
        .filter(
            vehicle=vehicle,
            status=ParkingRecord.Status.ACTIVE,
        )
        .order_by("-check_in_time", "-pk")
        .first()
    )
    if record is None:
        raise NotFound(
            "No active parking session was found for this vehicle."
        )

    checkout_time = timezone.now()
    if checkout_time < record.check_in_time:
        raise Conflict("Checkout time cannot be earlier than the check-in time.")

    # Fee calculation remains a documented billing follow-up. Do not populate
    # fee_amount until the tariff and penalty rules are agreed and integrated.
    record.check_out_time = checkout_time
    record.status = ParkingRecord.Status.COMPLETED
    record.save(update_fields=["check_out_time", "status"])

    # The slot release is in the same outer transaction, so a failure rolls
    # both the record completion and slot change back.
    release_slot(record.slot_id)
    record.refresh_from_db()
    return record
