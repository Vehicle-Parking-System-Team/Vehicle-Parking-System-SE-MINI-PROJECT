"""Admin-only occupancy and collected-revenue APIs (US-26/US-27)."""

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin
from .serializers import OccupancyQuerySerializer, RevenueQuerySerializer
from .revenue import revenue_report
from .services import occupancy_report


@method_decorator(never_cache, name='dispatch')
class OccupancyReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        query = OccupancyQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(occupancy_report(**query.validated_data))


@method_decorator(never_cache, name='dispatch')
class RevenueReportView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        query = RevenueQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        return Response(revenue_report(**query.validated_data))
