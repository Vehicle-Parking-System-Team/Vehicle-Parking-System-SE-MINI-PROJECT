from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from .models import AuditEvent
from .serializers import AuditEventFilterSerializer, AuditEventSerializer


class AuditEventPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


@method_decorator(never_cache, name='dispatch')
class AuditEventListView(APIView):
    """Admin-only, chronological, read-only access to the audit trail."""

    permission_classes = [IsAuthenticated, IsAdmin]
    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        events = AuditEvent.objects.all()
        filters = AuditEventFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        values = filters.validated_data
        for field in ('event_type', 'actor_id', 'resource_type'):
            if field in values:
                events = events.filter(**{field: values[field]})
        if 'actor' in values:
            events = events.filter(Q(actor_username__icontains=values['actor']) | Q(actor_id=values['actor']))
        if 'start' in values:
            events = events.filter(occurred_at__gte=values['start'])
        if 'end' in values:
            events = events.filter(occurred_at__lt=values['end'])

        paginator = AuditEventPagination()
        page = paginator.paginate_queryset(events, request, view=self)
        return paginator.get_paginated_response(AuditEventSerializer(page, many=True).data)
