from django.urls import path

from .views import DashboardMetricsView, OccupancyReportView, RevenueReportView
from .views import ReportExportView

app_name = 'reports'

urlpatterns = [
    path('export/', ReportExportView.as_view(), name='export'),
    path('dashboard/', DashboardMetricsView.as_view(), name='dashboard'),
    path('occupancy/', OccupancyReportView.as_view(), name='occupancy'),
    path('revenue/', RevenueReportView.as_view(), name='revenue'),
]
