from django.urls import path
from .availability import ParkingAvailabilityView

from .views import (
    ParkingSlotDetailView,
    ParkingSlotListCreateView,
    ParkingSlotStatusView,
    ParkingZoneDetailView,
    ParkingZoneListCreateView,
)

app_name = 'parking_slots'

urlpatterns = [
    path('availability/', ParkingAvailabilityView.as_view(), name='availability'),
    path('zones/', ParkingZoneListCreateView.as_view(), name='zone-list-create'),
    path('zones/<int:pk>/', ParkingZoneDetailView.as_view(), name='zone-detail'),
    path('slots/', ParkingSlotListCreateView.as_view(), name='slot-list-create'),
    path('slots/<int:pk>/', ParkingSlotDetailView.as_view(), name='slot-detail'),
    path(
        'slots/<int:pk>/status/',
        ParkingSlotStatusView.as_view(),
        name='slot-status',
    ),
]
