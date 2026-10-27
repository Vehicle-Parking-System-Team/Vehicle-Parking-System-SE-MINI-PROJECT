from django.urls import path

from .views import (
    ParkingHistoryView,
    VehicleCheckInView,
    VehicleCheckOutView,
)


app_name = "operations"

urlpatterns = [
    path(
        "check-in/",
        VehicleCheckInView.as_view(),
        name="check-in",
    ),
    path(
        "check-out/",
        VehicleCheckOutView.as_view(),
        name="check-out",
    ),
    path(
        "history/",
        ParkingHistoryView.as_view(),
        name="history",
    ),
]
