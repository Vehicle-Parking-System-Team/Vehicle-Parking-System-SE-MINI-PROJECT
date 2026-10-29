from django.urls import path
from .views import ReservationCreateView

app_name = 'reservations'
urlpatterns = [
    path('', ReservationCreateView.as_view(), name='reservation-create'),
]
