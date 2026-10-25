
from django.urls import path

from .views import ParkingHistoryView, VehicleCheckInView


app_name = "operations"

urlpatterns = [
    path(
        "check-in/",
        VehicleCheckInView.as_view(),
        name="check-in",
    ),
    path(
        "history/",
        ParkingHistoryView.as_view(),
        name="history",
    ),
]
