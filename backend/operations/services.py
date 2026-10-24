from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound

from common.exceptions import Conflict
from parking_slots.models import ParkingSlot
from parking_slots.services import occupy_slot
from vehicles.services import get_vehicle_by_registration_number

from .models import ParkingSession


@transaction.atomic
def check_in_vehicle(registration_number):
    """
    Check in a registered vehicle and allocate a compatible parking slot.
    """

    # 1. Find the registered vehicle.
    vehicle = get_vehicle_by_registration_number(registration_number)

    if vehicle is None:
        raise NotFound("No registered vehicle found with this registration number.")

    # 2. Prevent duplicate active parking sessions.
    if ParkingSession.objects.filter(
        vehicle=vehicle,
        status=ParkingSession.Status.ACTIVE,
    ).exists():
        raise Conflict("This vehicle already has an active parking session.")

    # 3. Find available slots compatible with the vehicle.
    slots = ParkingSlot.objects.filter(
        is_active=True,
        zone__is_active=True,
        status=ParkingSlot.Status.AVAILABLE,
    ).filter(
        Q(vehicle_type__iexact=vehicle.vehicle_type)
        | Q(vehicle_type__iexact="any")
    ).select_related(
        "zone"
    ).order_by(
        "zone__name",
        "slot_number",
        "pk",
    )

    # 4. Try compatible slots until one can be occupied.
    for candidate in slots:
        try:
            occupied_slot = occupy_slot(candidate.pk)
        except Conflict:
            # Another operation may have taken this slot.
            continue

        # 5. Create the parking session in the same transaction.
        # If creation fails, the slot occupation must roll back too.
        try:
            with transaction.atomic():
                session = ParkingSession.objects.create(
                    vehicle=vehicle,
                    slot=occupied_slot,
                    status=ParkingSession.Status.ACTIVE,
                )
        except IntegrityError:
            raise Conflict(
                "The vehicle or slot already has an active parking session."
            )

        return session

    # 6. No compatible slot could be allocated.
    raise Conflict(
        "Facility Full: no compatible parking slots are currently available."
    )