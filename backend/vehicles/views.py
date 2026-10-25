from django.db import IntegrityError, transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import Conflict
from vehicles.models import Vehicle
from vehicles.serializers import VehicleSerializer


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

        # Ownership and role authorization check (FR-02 / FR-16)
        is_owner = vehicle.owner == request.user
        is_admin_or_operator = (
            getattr(request.user, 'role', None) in ('Admin', 'Operator')
            or getattr(request.user, 'is_staff', False)
            or getattr(request.user, 'is_superuser', False)
        )
        if not (is_owner or is_admin_or_operator):
            raise PermissionDenied('You do not have permission to access this vehicle record.')

        return vehicle

    def get(self, request, pk=None, plate=None):
        """Retrieve vehicle details by ID or normalized license plate."""
        vehicle = self._get_vehicle(request, pk=pk, plate=plate)
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
