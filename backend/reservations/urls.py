from django.urls import path
from .views import ReservationCreateView, ReservationDetailView

app_name = 'reservations'
urlpatterns = [
    path('', ReservationCreateView.as_view(), name='reservation-create'),
    path('<int:pk>/', ReservationDetailView.as_view(), name='reservation-detail'),
]
