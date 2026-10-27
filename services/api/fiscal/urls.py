from django.urls import path

from fiscal import views

urlpatterns = [
    path("fiscal/status/", views.StatusView.as_view(), name="fiscal-status"),
    path("fiscal/settings/", views.SettingsView.as_view(), name="fiscal-settings"),
    path("fiscal/documents/", views.DocumentListView.as_view(), name="fiscal-documents"),
    path(
        "fiscal/documents/<uuid:doc_id>/submit/", views.SubmitView.as_view(), name="fiscal-submit"
    ),
    path(
        "fiscal/documents/<uuid:doc_id>/reconcile/",
        views.ReconcileView.as_view(),
        name="fiscal-reconcile",
    ),
]
