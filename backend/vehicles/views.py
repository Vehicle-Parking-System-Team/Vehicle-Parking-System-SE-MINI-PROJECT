from django.db import IntegrityError, transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import Conflict
from vehicles.models import Vehicle
from vehicles.serializers import VehicleSearchResultSerializer, VehicleSerializer


class VehicleRegistrationView(APIView):
    """
    Vehicle Registration Endpoint (US-05 / FR-01).
    Registers an arriving or customer vehicle with plate number, vehicle class,
    and owner information. Enforces uniqueness and authenticated user ownership.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve registered vehicles owned by the authenticated user."""
        vehicles = Vehicle.objects.filter(owner=request.user)
        serializer = VehicleSerializer(vehicles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Register a new vehicle with plate normalization and duplicate conflict protection."""
        serializer = VehicleSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                vehicle = serializer.save(owner=request.user)
        except IntegrityError:
            # Catch concurrent uniqueness violation
            raise Conflict('A vehicle with this registration number already exists.')

        output_serializer = VehicleSerializer(vehicle)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class VehicleDetailView(APIView):
    """
    Vehicle Profile and Detail Update Endpoint (US-06 / FR-02 / TC-UC02-API-002).
    Allows an authorized user to inspect and update vehicle profile and registration details.
    Enforces ownership isolation, duplicate prevention, and US-31 error contract.
    """

    permission_classes = [permissions.IsAuthenticated]

    def _get_vehicle(self, request, pk=None, plate=None):
        from rest_framework.exceptions import NotFound, PermissionDenied
        from vehicles.services import get_vehicle_by_id, get_vehicle_by_plate

        if pk is not None:
            vehicle = get_vehicle_by_id(pk)
        elif plate is not None:
            vehicle = get_vehicle_by_plate(plate)
        else:
            raise NotFound('Vehicle record not found.')

        if not vehicle:
            raise NotFound('Vehicle record not found.')

        # Ownership / Role authorization check (FR-16 / SAD §3.4.3)
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            role = getattr(request.user, 'role', None)
            is_privileged = (
                role in ['Admin', 'Operator']
                or getattr(request.user, 'is_staff', False)
                or getattr(request.user, 'is_superuser', False)
            )
            if not is_privileged and vehicle.owner != request.user:
                raise PermissionDenied('You do not have permission to access this vehicle record.')
        else:
            # Modification (PUT, PATCH, DELETE) requires object-level ownership
            # Operators cannot modify other customers' vehicles (PR #66 Review Fix)
            if vehicle.owner != request.user:
                raise PermissionDenied('You do not have permission to modify this vehicle record.')

        return vehicle

    def get(self, request, pk=None, plate=None):
        """Retrieve vehicle details by ID or normalized license plate."""
        vehicle = self._get_vehicle(request, pk=pk, plate=plate)
        include_status = request.query_params.get('include_status', '').lower() in ['true', '1', 'yes']
        if include_status:
            from vehicles.services import get_vehicle_parking_status
            parking_status = get_vehicle_parking_status(vehicle)
            serializer = VehicleSearchResultSerializer(vehicle, context={'parking_status': parking_status})
        else:
            serializer = VehicleSerializer(vehicle)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk=None, plate=None):
        """Full update of vehicle profile details."""
        vehicle = self._get_vehicle(request, pk=pk, plate=plate)
        serializer = VehicleSerializer(
            vehicle,
            data=request.data,
            partial=False,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                updated = serializer.save()
        except IntegrityError:
            raise Conflict('A vehicle with this registration number already exists.')

        return Response(VehicleSerializer(updated).data, status=status.HTTP_200_OK)

    def patch(self, request, pk=None, plate=None):
        """Partial update of vehicle profile details."""
        vehicle = self._get_vehicle(request, pk=pk, plate=plate)
        serializer = VehicleSerializer(
            vehicle,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                updated = serializer.save()
        except IntegrityError:
            raise Conflict('A vehicle with this registration number already exists.')

        return Response(VehicleSerializer(updated).data, status=status.HTTP_200_OK)


class VehicleSearchView(APIView):
    """
    Vehicle Search & Current Status Endpoint (US-07 / FR-11 / TC-UC02-API-001, TC-UC02-API-002).
    Allows authorized users or operators to search for a vehicle by license plate
    and inspect its current parking status.
    - Admin / Operator: permitted to search any vehicle.
    - Customer: permitted to search own vehicles.
    Returns vehicle details plus live parking status (is_parked, slot, zone, floor).
    Returns HTTP 404 if vehicle is not found (FR-14 structured format).
    Returns HTTP 403 if Customer attempts to inspect another customer's vehicle.
    Returns HTTP 400 if license plate query parameter is missing or empty.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, plate=None):
        search_plate = plate or request.query_params.get('plate') or request.query_params.get('q')
        if not search_plate or not str(search_plate).strip():
            return Response(
                {
                    'error': 'A license plate or registration number is required to search.',
                    'code': 'MISSING_SEARCH_QUERY',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from vehicles.services import search_vehicle_by_plate
        try:
            result = search_vehicle_by_plate(search_plate, requesting_user=request.user)
        except ValueError as err:
            return Response(
                {
                    'error': str(err),
                    'code': 'INVALID_SEARCH_QUERY',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if isinstance(result, list):
            data = [
                VehicleSearchResultSerializer(v, context={'parking_status': ps}).data
                for v, ps in result
            ]
            return Response(data, status=status.HTTP_200_OK)
        else:
            vehicle, parking_status = result
            serializer = VehicleSearchResultSerializer(vehicle, context={'parking_status': parking_status})
            return Response(serializer.data, status=status.HTTP_200_OK)
