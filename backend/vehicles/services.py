from django.db import IntegrityError, transaction
from common.exceptions import Conflict
from vehicles.models import Vehicle


def normalize_registration_number(registration_number: str) -> str:
    """
    Normalizes a vehicle registration number / license plate.
    Trims leading/trailing whitespace and converts to uppercase.
    Does not impose an overly restrictive alphanumeric regex.
    """
    if not registration_number:
        return ''
    return str(registration_number).strip().upper()


def get_vehicle_by_registration_number(registration_number: str) -> Vehicle | None:
    """
    Retrieves a Vehicle record by its normalized registration number.
    Returns None if no matching vehicle exists.
    """
    normalized = normalize_registration_number(registration_number)
    if not normalized:
        return None
    try:
        return Vehicle.objects.get(registration_number=normalized)
    except Vehicle.DoesNotExist:
        return None


def get_vehicle_by_plate(plate: str) -> Vehicle | None:
    """
    Direct alias for get_vehicle_by_registration_number.
    Standardized interface for Member 3 check-in workflow integration (US-17 / FR-05).
    """
    return get_vehicle_by_registration_number(plate)


def register_vehicle(
    owner,
    registration_number: str,
    vehicle_type: str,
    owner_name: str = '',
    owner_phone: str = '',
) -> Vehicle:
    """
    Registers a new vehicle record under the provided authenticated owner.
    Enforces normalized plate uniqueness and raises Conflict (HTTP 409) if duplicate.
    """
    if not owner:
        raise ValueError('A valid owner is required.')

    valid_types = [c[0] for c in Vehicle.VEHICLE_TYPE_CHOICES]
    if vehicle_type not in valid_types:
        raise ValueError(f'Invalid vehicle type: {vehicle_type}. Must be one of {valid_types}.')

    normalized_plate = normalize_registration_number(registration_number)
    if not normalized_plate:
        raise ValueError('Registration number cannot be empty.')
    if len(normalized_plate) > 20:
        raise ValueError('Registration number cannot exceed 20 characters.')

    # Explicit domain conflict check (US-31 error contract)
    if Vehicle.objects.filter(registration_number=normalized_plate).exists():
        raise Conflict('A vehicle with this registration number already exists.')

    try:
        with transaction.atomic():
            return Vehicle.objects.create(
                registration_number=normalized_plate,
                vehicle_type=vehicle_type,
                owner=owner,
                owner_name=owner_name.strip() if owner_name else (owner.get_full_name() or owner.username),
                owner_phone=owner_phone.strip() if owner_phone else '',
            )
    except IntegrityError:
        # Catch concurrent race condition collisions and fail closed with 409 Conflict
        raise Conflict('A vehicle with this registration number already exists.')


def get_vehicle_by_id(vehicle_id: int) -> Vehicle | None:
    """
    Retrieves a Vehicle record by primary key id (US-06 / FR-02).
    Returns None if no matching vehicle exists or invalid ID format.
    """
    try:
        return Vehicle.objects.get(pk=vehicle_id)
    except (Vehicle.DoesNotExist, ValueError):
        return None


def update_vehicle(
    vehicle: Vehicle,
    registration_number: str | None = None,
    vehicle_type: str | None = None,
    owner_name: str | None = None,
    owner_phone: str | None = None,
) -> Vehicle:
    """
    Updates an existing Vehicle record (US-06 / FR-02).
    Enforces normalized plate uniqueness excluding the current vehicle,
    validates vehicle type if updated, and atomically persists modifications.
    """
    if not vehicle:
        raise ValueError('A valid vehicle instance is required.')

    if vehicle_type is not None:
        valid_types = [c[0] for c in Vehicle.VEHICLE_TYPE_CHOICES]
        if vehicle_type not in valid_types:
            raise ValueError(f'Invalid vehicle type: {vehicle_type}. Must be one of {valid_types}.')
        vehicle.vehicle_type = vehicle_type

    if registration_number is not None:
        normalized_plate = normalize_registration_number(registration_number)
        if not normalized_plate:
            raise ValueError('Registration number cannot be empty.')
        if len(normalized_plate) > 20:
            raise ValueError('Registration number cannot exceed 20 characters.')

        duplicate_qs = Vehicle.objects.filter(registration_number=normalized_plate).exclude(pk=vehicle.pk)
        if duplicate_qs.exists():
            raise Conflict('A vehicle with this registration number already exists.')
        vehicle.registration_number = normalized_plate

    if owner_name is not None:
        vehicle.owner_name = owner_name.strip()

    if owner_phone is not None:
        vehicle.owner_phone = owner_phone.strip()

    try:
        with transaction.atomic():
            vehicle.save()
            return vehicle
    except IntegrityError:
        raise Conflict('A vehicle with this registration number already exists.')
