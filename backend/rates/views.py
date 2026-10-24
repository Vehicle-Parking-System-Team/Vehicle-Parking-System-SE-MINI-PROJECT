
from rest_framework import generics

from rates.models import ParkingRate
from rates.permissions import IsAdminOrReadOnly
from rates.serializers import ParkingRateSerializer


class ParkingRateListCreateView(generics.ListCreateAPIView):
    """List configured parking rates or create a rate as an administrator."""

    queryset = ParkingRate.objects.all()
    serializer_class = ParkingRateSerializer
    permission_classes = [IsAdminOrReadOnly]


class ParkingRateDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a configured parking rate."""

    queryset = ParkingRate.objects.all()
    serializer_class = ParkingRateSerializer
    permission_classes = [IsAdminOrReadOnly]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']
