
from django.urls import path

from rates.views import ParkingRateDetailView, ParkingRateListCreateView

app_name = 'rates'

urlpatterns = [
    path('', ParkingRateListCreateView.as_view(), name='rate_list_create'),
    path('<int:pk>/', ParkingRateDetailView.as_view(), name='rate_detail'),
]
