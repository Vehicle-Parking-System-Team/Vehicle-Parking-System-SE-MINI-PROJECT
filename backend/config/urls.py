"""
URL configuration for Vehicle Parking System project.
"""
from django.contrib import admin
from django.urls import path, include
from vehicles.views import VehicleRegistrationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/v1/vehicles/', include('vehicles.urls')),
    path('api/parking/', include('parking_slots.urls')),
    path('api/vehicles/', VehicleRegistrationView.as_view(), name='vehicles_root'),
    path('api/v1/rates/', include('rates.urls')),
]
