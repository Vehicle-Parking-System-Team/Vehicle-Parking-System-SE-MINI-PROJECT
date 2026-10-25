from django.urls import path

from .views import VehicleCheckInView, VehicleCheckOutView


app_name = "operations"

urlpatterns = [
    path('check-out/', VehicleCheckOutView.as_view(), name='check-out'),
    path(
        "check-in/",
        VehicleCheckInView.as_view(),
        name="check-in",
    ),
]
