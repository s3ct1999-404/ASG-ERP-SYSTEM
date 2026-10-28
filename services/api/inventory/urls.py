from django.urls import path

from inventory import views

urlpatterns = [
    path("inventory/receipts/", views.ReceiptView.as_view(), name="stock-receipt"),
    path("inventory/adjustments/", views.AdjustmentView.as_view(), name="stock-adjust"),
    path("inventory/stock/", views.StockView.as_view(), name="stock"),
    path("inventory/movements/", views.MovementListView.as_view(), name="stock-movements"),
]
