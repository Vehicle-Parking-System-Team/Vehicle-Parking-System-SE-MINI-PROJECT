from rest_framework import generics
from accounts.permissions import has_roles
from .serializers import ReservationCreateSerializer


class ReservationCreateView(generics.CreateAPIView):
    serializer_class = ReservationCreateSerializer
    permission_classes = [has_roles('Customer', 'Operator')]
    http_method_names = ['post', 'options']
