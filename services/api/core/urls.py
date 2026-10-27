from django.db.transaction import non_atomic_requests
from django.urls import path
from django.views.decorators.http import require_GET  # noqa: F401

from core.views import LiveView, ReadyView

# Probes must not open a request transaction (they must work when the DB is down).
urlpatterns = [
    path("health/live/", non_atomic_requests(LiveView.as_view()), name="health-live"),
    path("health/ready/", non_atomic_requests(ReadyView.as_view()), name="health-ready"),
]
