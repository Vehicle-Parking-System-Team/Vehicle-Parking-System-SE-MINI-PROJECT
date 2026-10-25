import json

from django.core.signing import Signer
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound, ValidationError

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot
from parking_slots.services import occupy_slot
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


def create_signed_ticket(record):
    """
    Generate a signed QR-ready ticket payload.

    The token contains:
    sessionId, vehiclePlate, slotNumber, checkInTime, signature.
    """
    payload = {
        "sessionId": record.pk,
        "vehiclePlate": record.vehicle.registration_number,
        "slotNumber": record.slot.slot_number,
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
    """
    Check in a registered vehicle and allocate a compatible parking slot.

    Args:
        registration_number: Registered vehicle's license plate.
        operator: Authenticated user performing the check-in.
        slot_id: Optional manually selected parking slot primary key.

    Returns:
        The newly created ParkingRecord.

    Raises:
        NotFound: Vehicle or explicitly selected slot does not exist.
        ValidationError: Invalid vehicle registration or incompatible slot.
        Conflict: Duplicate active record, unavailable slot, or no
                  compatible available slot.
    """

    # 1. Require an authenticated operator.
    if operator is None or not getattr(operator, "is_authenticated", False):
        raise ValidationError(
            {"operator": "An authenticated operator is required."}
        )

    # 2. Normalize and validate the registration number.
    plate = normalize_registration_number(registration_number)

    if not plate:
        raise ValidationError(
            {
                "registration_number":
                    "A vehicle registration number is required."
            }
        )

    # 3. Lock the vehicle row to serialize check-ins for the same vehicle
    # on databases that support SELECT FOR UPDATE.
    vehicle = (
        Vehicle.objects.select_for_update()
        .filter(registration_number=plate)
        .first()
    )

    if vehicle is None:
        raise NotFound(
            "No registered vehicle was found with this registration number."
        )

    # 4. Prevent a vehicle from having multiple active parking records.
    if ParkingRecord.objects.filter(
        vehicle=vehicle,
        status=ParkingRecord.Status.ACTIVE,
    ).exists():
        raise Conflict(
            "This vehicle already has an active parking record."
        )

    # 5. Find active, available slots compatible with this vehicle.
    compatible_slots = ParkingSlot.objects.filter(
        Q(vehicle_type__iexact=vehicle.vehicle_type)
        | Q(vehicle_type__iexact="any")
    )

    if slot_id is not None:
        # A manually selected slot must be validated explicitly.
        candidate = (
            ParkingSlot.objects.select_related("zone")
            .filter(pk=slot_id)
            .first()
        )

        if candidate is None:
            raise NotFound("The selected parking slot does not exist.")

        if not candidate.is_active or not candidate.zone.is_active:
            raise Conflict(
                "The selected slot or its zone is inactive."
            )

        if candidate.status != ParkingSlot.Status.AVAILABLE:
            raise Conflict(
                "The selected parking slot is not available."
            )

        if not _is_compatible_slot(candidate, vehicle):
            raise ValidationError(
                {
                    "slot_id":
                        "The selected slot is incompatible with this vehicle."
                }
            )

        candidate_ids = [candidate.pk]

    else:
        # Automatic allocation recommends the first compatible slot.
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

    # 6. Lock and occupy candidates, rechecking compatibility after
    # occupy_slot() refreshes the slot from the database.
    for candidate_id in candidate_ids:
        try:
            with transaction.atomic():
                slot = occupy_slot(candidate_id)

                # IMPORTANT: this check happens after the slot lifecycle
                # service has locked and refreshed the slot.
                if not _is_compatible_slot(slot, vehicle):
                    raise _SlotCompatibilityChanged(
                        "The slot is no longer compatible."
                    )

                # 7. Persist the record and authenticated operator.
                record = ParkingRecord.objects.create(
                    vehicle=vehicle,
                    slot=slot,
                    operator=operator,
                    status=ParkingRecord.Status.ACTIVE,
                )

                # 8. Generate the signed ticket after the database ID
                # exists. Keep token creation in the same transaction.
                record.ticket_qr_token = create_signed_ticket(record)
                record.save(update_fields=["ticket_qr_token"])

            return record

        except _SlotCompatibilityChanged:
            # The nested transaction rolls back the occupation.
            if slot_id is not None:
                raise ValidationError(
                    {
                        "slot_id":
                            "The selected slot is no longer compatible "
                            "with this vehicle. Please choose another slot."
                    }
                ) from None

            # Automatic allocation can try another compatible candidate.
            continue

        except Conflict:
            # The slot may have become unavailable after candidate discovery.
            if slot_id is not None:
                raise

            continue

        except IntegrityError:
            # The inner transaction/savepoint has rolled back. Check whether
            # a concurrent request created the active record first.
            if ParkingRecord.objects.filter(
                vehicle=vehicle,
                status=ParkingRecord.Status.ACTIVE,
            ).exists():
                raise Conflict(
                    "This vehicle already has an active parking record."
                ) from None

            if ParkingRecord.objects.filter(
                slot_id=candidate_id,
                status=ParkingRecord.Status.ACTIVE,
            ).exists():
                if slot_id is not None:
                    raise Conflict(
                        "The selected slot was allocated by another request."
                    ) from None

                continue

            # Unexpected integrity errors should not be hidden.
            raise

    # 9. No candidate could be allocated.
    raise Conflict(
        "Facility Full: no compatible parking slots are currently available."
    )