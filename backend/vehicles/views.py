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
