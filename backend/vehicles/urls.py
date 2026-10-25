from django.urls import path
from vehicles.views import VehicleDetailView, VehicleRegistrationView, VehicleSearchView

app_name = 'vehicles'

urlpatterns = [
    path('', VehicleRegistrationView.as_view(), name='vehicle_list_create'),
    path('search/', VehicleSearchView.as_view(), name='vehicle_search'),
    path('search/<str:plate>/', VehicleSearchView.as_view(), name='vehicle_search_by_plate'),
    path('<int:pk>/', VehicleDetailView.as_view(), name='vehicle_detail'),
    path('by-plate/<str:plate>/', VehicleDetailView.as_view(), name='vehicle_detail_by_plate'),
]
