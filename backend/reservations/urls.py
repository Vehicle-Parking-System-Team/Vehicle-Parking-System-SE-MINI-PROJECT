from django.urls import path
from .views import ReservationCreateView, ReservationDetailView, ReservationListView

app_name = 'reservations'
urlpatterns = [
    path('', ReservationCreateView.as_view(), name='reservation-create'),
    path('list/', ReservationListView.as_view(), name='reservation-list'),
    path('<int:pk>/', ReservationDetailView.as_view(), name='reservation-detail'),
]
