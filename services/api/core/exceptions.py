"""Uniform API error envelope. Never leaks internals; carries the request id."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import exceptions as drf
from rest_framework.response import Response
from rest_framework.views import exception_handler


class DomainError(Exception):
    """A business-rule violation that is the caller's fault (HTTP 409/422)."""

    status_code = 422
    code = "domain_error"

    def __init__(self, message: str, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, DomainError):
        return Response(
            {"error": {"code": exc.code, "message": exc.message}}, status=exc.status_code
        )
    if isinstance(exc, ValidationError):
        return Response(
            {"error": {"code": "invalid", "message": "; ".join(exc.messages)}}, status=422
        )
    if isinstance(exc, PermissionDenied):
        exc = drf.PermissionDenied()
    if isinstance(exc, Http404):
        exc = drf.NotFound()
    response = exception_handler(exc, context)
    if response is not None:
        detail = response.data
        response.data = {
            "error": {
                "code": getattr(exc, "default_code", "error"),
                "message": detail.get("detail")
                if isinstance(detail, dict) and "detail" in detail
                else detail,
            }
        }
    return response
