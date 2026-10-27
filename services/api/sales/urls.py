from django.urls import path

from sales import views

urlpatterns = [
    path("sales/invoices/", views.InvoiceListCreate.as_view(), name="invoices"),
    path(
        "sales/invoices/<uuid:invoice_id>/payments/",
        views.PaymentCreate.as_view(),
        name="invoice-payment",
    ),
    path("pos/sales/", views.PosSale.as_view(), name="pos-sale"),
]
