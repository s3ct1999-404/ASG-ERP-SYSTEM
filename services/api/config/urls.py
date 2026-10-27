from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("identity.urls")),
    path("api/v1/", include("tenancy.urls")),
    path("api/v1/", include("masterdata.urls")),
    path("api/v1/", include("inventory.urls")),
    path("api/v1/", include("accounting.urls")),
    path("api/v1/", include("sales.urls")),
    path("api/v1/", include("fiscal.urls")),
]
