from rest_framework import generics
from accounts.permissions import IsCustomer
from .serializers import ReservationCreateSerializer


class ReservationCreateView(generics.CreateAPIView):
    serializer_class = ReservationCreateSerializer
    permission_classes = [IsAuthenticatedAndActive]
    http_method_names = ['post', 'options']
