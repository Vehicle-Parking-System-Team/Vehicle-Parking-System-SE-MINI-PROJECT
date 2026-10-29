from datetime import timedelta

from rest_framework import generics, status
from rest_framework.response import Response
from accounts.permissions import has_roles, IsAuthenticatedAndActive
from .serializers import (
    ReservationCreateSerializer, ReservationChangeSerializer,
    ReservationDetailSerializer,
)
from .services import change_reservation


class ReservationCreateView(generics.CreateAPIView):
    serializer_class = ReservationCreateSerializer
    permission_classes = [has_roles('Customer', 'Operator')]
    http_method_names = ['post', 'options']


class ReservationDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedAndActive]
    http_method_names = ['patch', 'delete', 'options']

    def patch(self, request, pk):
        serializer = ReservationChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start = serializer.validated_data['start_time']
        reservation = change_reservation(
            reservation_id=pk, actor=request.user,
            start_time=start,
            end_time=start + timedelta(
                minutes=serializer.validated_data['duration_minutes'],
            ),
        )
        return Response(ReservationDetailSerializer(reservation).data)

    def delete(self, request, pk):
        reservation = change_reservation(
            reservation_id=pk, actor=request.user, cancel=True,
        )
        return Response(ReservationDetailSerializer(reservation).data, status=status.HTTP_200_OK)
