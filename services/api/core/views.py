"""Health endpoints.

These are the only endpoints that explicitly opt out of the deny-by-default
permission policy. They expose no version, host, or dependency detail.
"""

from __future__ import annotations

import logging

from django.db import DatabaseError, connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import HealthSerializer

logger = logging.getLogger(__name__)


class LiveView(APIView):
    """Liveness: the process is up and serving requests."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]  # explicit, reviewed exception to deny-by-default

    @extend_schema(responses={200: HealthSerializer}, summary="Liveness probe")
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class ReadyView(APIView):
    """Readiness: the process can reach its database."""

    authentication_classes: list[type] = []
    permission_classes = [AllowAny]  # explicit, reviewed exception to deny-by-default

    @extend_schema(
        responses={200: HealthSerializer, 503: HealthSerializer},
        summary="Readiness probe",
    )
    def get(self, request: Request) -> Response:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except DatabaseError:
            # Details go to the log only, never into the response.
            logger.exception("readiness check failed: database unavailable")
            return Response({"status": "unavailable"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"status": "ok"})
