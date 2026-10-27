from django.urls import path

from accounting import views

urlpatterns = [
    path("accounting/accounts/", views.AccountListView.as_view(), name="accounts"),
    path("accounting/journals/", views.JournalView.as_view(), name="journals"),
    path(
        "accounting/journals/<uuid:entry_id>/reverse/",
        views.ReverseView.as_view(),
        name="journal-reverse",
    ),
    path("accounting/periods/", views.PeriodView.as_view(), name="periods"),
    path("accounting/<uuid:company_id>/<str:report>/", views.ReportView.as_view(), name="report"),
]
