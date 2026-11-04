from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAuthenticatedAndActive
from .models import Notification
from .services import notify_expiring_reservations


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'kind', 'message', 'created_at', 'read_at')


class InboxQuerySerializer(serializers.Serializer):
    unread_only = serializers.BooleanField(default=False)


@method_decorator(never_cache, name='dispatch')
class NotificationListView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def get(self, request):
        query = InboxQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        notify_expiring_reservations(request.user)
        inbox = Notification.objects.filter(recipient=request.user)
        unread = inbox.filter(read_at__isnull=True)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        rows = paginator.paginate_queryset(unread if query.validated_data['unread_only'] else inbox, request)
        response = paginator.get_paginated_response(NotificationSerializer(rows, many=True).data)
        response.data['unread_count'] = response.data['count'] if query.validated_data['unread_only'] else unread.count()
        return response


@method_decorator(never_cache, name='dispatch')
class NotificationReadView(APIView):
    permission_classes = [IsAuthenticatedAndActive]

    def post(self, request, pk):
        inbox = Notification.objects.filter(recipient=request.user)
        notification = get_object_or_404(inbox, pk=pk)
        inbox.filter(pk=pk, read_at__isnull=True).update(read_at=timezone.now())
        notification.refresh_from_db()
        return Response({'id': pk, 'read_at': notification.read_at,
                         'unread_count': inbox.filter(read_at__isnull=True).count()})
