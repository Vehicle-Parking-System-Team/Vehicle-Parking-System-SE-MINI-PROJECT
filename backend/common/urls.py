from django.urls import path

from .views import AuditEventListView

app_name = 'common'

urlpatterns = [
    path('', AuditEventListView.as_view(), name='audit-event-list'),
]
