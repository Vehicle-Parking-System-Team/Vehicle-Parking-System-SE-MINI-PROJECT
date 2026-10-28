from django.urls import path

from .views import ReceiptCollectionView, ReceiptDetailView, ReceiptPrintableView


app_name = 'billing'

urlpatterns = [
    path('', ReceiptCollectionView.as_view(), name='receipt-create'),
    path('<uuid:receipt_number>/', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('<uuid:receipt_number>/print/', ReceiptPrintableView.as_view(), name='receipt-print'),
]
