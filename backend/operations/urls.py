from django.urls import path

from .views import VehicleCheckInView


app_name = "operations"

urlpatterns = [
    path(
        "check-in/",
        VehicleCheckInView.as_view(),
        name="check-in",
    ),
]