from django.urls import path

from .views import OccupancyReportView

app_name = 'reports'

urlpatterns = [
    path('occupancy/', OccupancyReportView.as_view(), name='occupancy'),
]
