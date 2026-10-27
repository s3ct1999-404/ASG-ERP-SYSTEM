from django.urls import path

from tenancy import views

urlpatterns = [
    path("me/", views.MeView.as_view(), name="me"),
    path("platform/tenants/", views.ProvisionTenantView.as_view(), name="tenant-provision"),
    path("permissions/", views.PermissionCatalogView.as_view(), name="permissions"),
    path("companies/", views.CompanyListView.as_view(), name="companies"),
    path("branches/", views.BranchListView.as_view(), name="branches"),
    path("roles/", views.RoleListView.as_view(), name="roles"),
    path("memberships/", views.MembershipListView.as_view(), name="memberships"),
    path(
        "memberships/<uuid:membership_id>/assignments/",
        views.AssignmentCreateView.as_view(),
        name="assignments",
    ),
]
