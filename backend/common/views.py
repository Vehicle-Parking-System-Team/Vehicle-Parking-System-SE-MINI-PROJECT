from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class AuditEventListView(APIView):
    """Admin-only, chronological, read-only access to the audit trail."""

    permission_classes = [IsAuthenticated, IsAdmin]
    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        events = AuditEvent.objects.all()
        event_type = request.query_params.get('event_type')
        actor_id = request.query_params.get('actor_id')
        if event_type:
            events = events.filter(event_type=event_type)
        if actor_id:
            events = events.filter(actor_id=actor_id)

        paginator = AuditEventPagination()
        page = paginator.paginate_queryset(events, request, view=self)
        return paginator.get_paginated_response(AuditEventSerializer(page, many=True).data)
