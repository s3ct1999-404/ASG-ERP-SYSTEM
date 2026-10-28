from django.urls import path

from masterdata import views

urlpatterns = [
    path("uoms/", views.UnitOfMeasureListView.as_view(), name="uoms"),
    path("tax-codes/", views.TaxCodeView.as_view(), name="tax-codes"),
    path("partners/", views.PartnerView.as_view(), name="partners"),
    path("products/", views.ProductView.as_view(), name="products"),
    path("warehouses/", views.WarehouseView.as_view(), name="warehouses"),
]
