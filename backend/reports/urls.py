from django.urls import path

from .views import OccupancyReportView, RevenueReportView

app_name = 'reports'

urlpatterns = [
    path('occupancy/', OccupancyReportView.as_view(), name='occupancy'),
    path('revenue/', RevenueReportView.as_view(), name='revenue'),
]
