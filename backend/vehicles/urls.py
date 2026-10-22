from django.urls import path
from vehicles.views import VehicleRegistrationView

app_name = 'vehicles'

urlpatterns = [
    path('', VehicleRegistrationView.as_view(), name='vehicle_list_create'),
]
