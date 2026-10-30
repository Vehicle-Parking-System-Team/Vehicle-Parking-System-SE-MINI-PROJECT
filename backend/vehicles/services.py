import re
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework.exceptions import NotFound, PermissionDenied
from common.exceptions import Conflict
from vehicles.models import Vehicle

# Anchored regex supporting standard state registrations and BH-series
REGISTRATION_NUMBER_PATTERN = re.compile(
    r'(?:[A-Z]{2}-?(?:[0-9]{1,2}-?)?[A-Z]{1,8}-?[0-9]{1,4}|[0-9]{2}-?BH-?[0-9]{4}-?[A-Z]{1,2})'
)


def normalize_registration_number(registration_number: str) -> str:
    """
    Return one canonical representation for supported plate separators.

    Hyphenated, space-separated, and compact alphanumeric plates are supported.
    Mixed separators, repeated hyphens, tabs, control characters, and other
    punctuation are deliberately not repaired; the format validator rejects them.
    """
    if not isinstance(registration_number, str):
        return ''

    normalized = registration_number.strip().upper()
    if not normalized:
        return ''

    # Do not turn illegal characters into a valid plate during sanitization.
    if not re.fullmatch(r'[A-Z0-9 -]+', normalized):
        return normalized

    if '-' in normalized:
        return re.sub(r' *- *', '-', normalized)

    if ' ' in normalized:
        parts = re.split(r' +', normalized)
        if len(parts) in (3, 4):
            return '-'.join(parts)

    return normalized


def is_registration_number_unique_violation(error: IntegrityError) -> bool:
    """
    Identify only the vehicle registration uniqueness constraint.

    Other integrity failures (for example a broken owner foreign key) must
    remain server errors rather than being mislabeled as duplicate plates.
    """
    cause = error.__cause__
    constraint_name = getattr(getattr(cause, 'diag', None), 'constraint_name', None)
    if constraint_name == 'vehicles_registration_number_key':
        return True

    database_message = str(cause or error).lower()
    return (
        'unique constraint failed: vehicles.registration_number' in database_message
        or (
            'duplicate key value violates unique constraint' in database_message
            and 'vehicles_registration_number' in database_message
        )
    )


def is_valid_registration_number(registration_number: str) -> bool:
    """
    Validates vehicle registration numbers according to documented supported formats:
    1. Standard State format: 2-letter state code + 1-2 digit RTO + 1-4 letter series + 1-4 digit serial
       (e.g., KA-01-AB-1234, DL3CBB1122, MH-12-CD-5678, KA-01-TEST-99).
    2. BH-Series format: 2-digit year + BH + 4-digit serial + 1-2 letter series
       (e.g., 22-BH-1234-AA, 22BH1234A).
    Enforces complete input anchoring (^...$) and rejects malformed prefixes, excess characters,
    trailing junk, and embedded substrings.
    """
    if not registration_number or not isinstance(registration_number, str):
        return False
    normalized = normalize_registration_number(registration_number)
    return len(normalized) <= 20 and bool(REGISTRATION_NUMBER_PATTERN.fullmatch(normalized))


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
    Validates registration number format against documented patterns.
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
    if not is_valid_registration_number(normalized_plate):
        raise ValueError('Invalid vehicle registration number format.')

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
    except IntegrityError as exc:
        if is_registration_number_unique_violation(exc):
            # The database unique constraint is the concurrency-safe authority.
            raise Conflict('A vehicle with this registration number already exists.') from exc
        raise


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
        if not is_valid_registration_number(normalized_plate):
            raise ValueError('Invalid vehicle registration number format.')

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
    except IntegrityError as exc:
        if is_registration_number_unique_violation(exc):
            raise Conflict('A vehicle with this registration number already exists.') from exc
        raise


def get_vehicle_parking_status(vehicle: Vehicle) -> dict:
    """
    Resolves the live parking status of a vehicle (US-07 / FR-11).
    Derives status directly from authoritative persisted ParkingRecord (US-17 / PR #67).
    Returns PARKED only when the vehicle has a valid active parking record.
    Returns NOT_PARKED when no active record exists (including completed historical records).
    Safely handles slot relationships and avoids N+1 queries using select_related.
    """
    if not vehicle or not getattr(vehicle, 'pk', None):
        return {
            'is_parked': False,
            'status': 'NOT_PARKED',
            'session_id': None,
            'check_in_time': None,
            'slot': None,
            'message': 'No vehicle specified.',
        }

    from operations.models import ParkingRecord

    active_record = (
        ParkingRecord.objects.filter(
            vehicle=vehicle,
            status=ParkingRecord.Status.ACTIVE,
        )
        .select_related('slot', 'slot__zone')
        .first()
    )

    if active_record and getattr(active_record, 'slot', None):
        slot = active_record.slot
        check_in_val = active_record.check_in_time
        check_in_str = check_in_val.isoformat() if hasattr(check_in_val, 'isoformat') else str(check_in_val)
        zone_name = slot.zone.name if getattr(slot, 'zone', None) else ''
        slot_num = slot.slot_number

        return {
            'is_parked': True,
            'status': 'PARKED',
            'session_id': active_record.pk,
            'check_in_time': check_in_str,
            'slot': {
                'id': slot.pk,
                'slot_number': slot_num,
                'zone': zone_name,
                'floor': getattr(slot, 'floor', None),
            },
            'message': f'Vehicle is currently parked in bay {slot_num}.',
        }

    return {
        'is_parked': False,
        'status': 'NOT_PARKED',
        'session_id': None,
        'check_in_time': None,
        'slot': None,
        'message': 'Vehicle is not currently parked in any slot.',
    }


def search_vehicles(search_query: str, requesting_user=None) -> list[tuple[Vehicle, dict]]:
    """
    Searches for vehicles by license plate (exact or partial matching) and resolves their live parking status.
    - Normalizes search string (case, whitespace, permitted separators).
    - Prevents unrestricted full-table searches (requires minimum 2 non-separator characters).
    - Enforces RBAC permissions:
      * Admin & Operator: permitted to search any vehicle.
      * Customer: restricted to own vehicles (cross-tenant queries are blocked).
    - Returns a list of (vehicle, parking_status) tuples.
    - Uses safe Django ORM queries with select_related to avoid N+1 queries.
    """
    if not search_query or not str(search_query).strip():
        raise ValueError('A license plate or registration number is required to search.')

    raw = str(search_query).strip()
    alphanumeric_chars = re.sub(r'[^A-Za-z0-9]', '', raw)
    if len(alphanumeric_chars) < 2:
        raise ValueError('Search query must contain at least 2 alphanumeric characters.')

    # Permission check
    is_privileged = False
    if requesting_user and hasattr(requesting_user, 'is_authenticated') and requesting_user.is_authenticated:
        role = getattr(requesting_user, 'role', None)
        is_privileged = (
            role in ['Admin', 'Operator']
            or getattr(requesting_user, 'is_staff', False)
            or getattr(requesting_user, 'is_superuser', False)
        )

    # First, attempt normalized exact lookup
    normalized_exact = normalize_registration_number(raw)

    # Check if exact match exists anywhere in the database
    exact_match = Vehicle.objects.filter(registration_number=normalized_exact).first()
    if exact_match:
        if not is_privileged and exact_match.owner != requesting_user:
            raise PermissionDenied('You do not have permission to view details for this vehicle.')
        return [(exact_match, get_vehicle_parking_status(exact_match))]

    # Build safe ORM query for partial search
    upper_query = raw.upper()
    collapsed = re.sub(r'\s+', '-', upper_query)
    clean_no_sep = re.sub(r'[-\s]', '', upper_query)

    query_filter = (
        Q(registration_number__icontains=upper_query)
        | Q(registration_number__icontains=collapsed)
    )
    if clean_no_sep:
        query_filter |= Q(registration_number__icontains=clean_no_sep)

    # Role scoping: Customer only searches own vehicles; Admin/Operator searches all
    if is_privileged:
        qs = Vehicle.objects.filter(query_filter).order_by('registration_number')
    else:
        qs = Vehicle.objects.filter(query_filter, owner=requesting_user).order_by('registration_number')

    results = list(qs[:50])
    if not results:
        raise NotFound(f'No vehicle found with registration number "{normalized_exact}".')

    return [(v, get_vehicle_parking_status(v)) for v in results]


def search_vehicle_by_plate(plate: str, requesting_user=None) -> tuple[Vehicle, dict] | list[tuple[Vehicle, dict]]:
    """
    Searches for a vehicle by license plate and resolves its parking status (US-07 / FR-11).
    Preserves existing exact-match behavior and response schema:
    If a single vehicle matches, returns (vehicle, parking_status).
    If multiple vehicles match, returns a list of (vehicle, parking_status) tuples.
    Raises NotFound (HTTP 404) if no vehicle matches.
    Raises PermissionDenied (HTTP 403) if requesting user lacks authorization.
    Raises ValueError (HTTP 400) if query is missing, empty, or too short.
    """
    results = search_vehicles(plate, requesting_user=requesting_user)
    if len(results) == 1:
        return results[0]
    return results

