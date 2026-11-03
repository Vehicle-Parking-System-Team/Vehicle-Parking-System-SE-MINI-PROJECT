from django.urls import path

from .views import DashboardMetricsView, OccupancyReportView, RevenueReportView

app_name = 'reports'

urlpatterns = [
    path('dashboard/', DashboardMetricsView.as_view(), name='dashboard'),
    path('occupancy/', OccupancyReportView.as_view(), name='occupancy'),
    path('revenue/', RevenueReportView.as_view(), name='revenue'),
]
