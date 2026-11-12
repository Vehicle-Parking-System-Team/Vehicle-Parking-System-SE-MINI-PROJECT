from datetime import timedelta

from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from .models import Reservation
from rest_framework.response import Response
from accounts.permissions import has_roles, IsAuthenticatedAndActive
from .serializers import (
    ReservationCreateSerializer, ReservationChangeSerializer,
    ReservationDetailSerializer,
)
from .services import change_reservation


class ReservationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReservationListView(generics.ListAPIView):
    serializer_class = ReservationDetailSerializer
    permission_classes = [IsAuthenticatedAndActive]
    pagination_class = ReservationPagination

    def get_queryset(self):
        queryset = Reservation.objects.select_related('customer', 'vehicle', 'slot')
        if self.request.user.role == 'Customer':
            queryset = queryset.filter(customer=self.request.user)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            if status_filter not in Reservation.Status.values:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'status': 'Invalid reservation status.'})
            queryset = queryset.filter(status=status_filter)
        return queryset


class ReservationCreateView(generics.CreateAPIView):
    serializer_class = ReservationCreateSerializer
    permission_classes = [has_roles('Customer', 'Operator')]
    http_method_names = ['get', 'post', 'options']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticatedAndActive()]
        return super().get_permissions()

    def get(self, request):
        view = ReservationListView.as_view()
        return view(request._request)


class ReservationDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedAndActive]
    http_method_names = ['get', 'patch', 'delete', 'options']

    def get(self, request, pk):
        from django.shortcuts import get_object_or_404
        queryset = Reservation.objects.select_related('customer', 'vehicle', 'slot')
        if request.user.role == 'Customer':
            queryset = queryset.filter(customer=request.user)
        reservation = get_object_or_404(queryset, pk=pk)
        return Response(ReservationDetailSerializer(reservation).data)

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
            reservation_id=pk, actor=request.user, cancel=True, request=request,
        )
        return Response(ReservationDetailSerializer(reservation).data, status=status.HTTP_200_OK)
