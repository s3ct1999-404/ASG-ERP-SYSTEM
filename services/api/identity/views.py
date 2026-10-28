from __future__ import annotations

from typing import Any, cast

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from audit.service import record
from identity.authentication import current_user
from identity.models import AuthToken, User

# Equalise timing for unknown users (reduces user enumeration).
_DUMMY_HASH = make_password("not-a-real-password")


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class LoginView(APIView):
    authentication_classes: list[type] = []
    permission_classes = [AllowAny]  # reviewed exception: this is the login endpoint
    throttle_classes = [LoginThrottle]

    @extend_schema(
        request=inline_serializer(
            "LoginRequest",
            {"email": serializers.EmailField(), "password": serializers.CharField()},
        ),
        responses={
            200: inline_serializer(
                "LoginResponse",
                {"token": serializers.CharField(), "expires_at": serializers.DateTimeField()},
            )
        },
        summary="Exchange credentials for a bearer token",
    )
    def post(self, request: Request) -> Response:
        data = cast(dict[str, Any], request.data)
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        user = User.objects.filter(email=email, is_active=True).first()
        ok = user is not None and user.check_password(password)
        if user is None:
            check_password(password, _DUMMY_HASH)
        if not ok or user is None:
            record(action="auth.login", outcome="denied", durable=True)
            return Response(
                {"error": {"code": "invalid_credentials", "message": "Invalid credentials."}},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        token, raw = AuthToken.issue(user)
        record(action="auth.login", outcome="success", actor_id=user.id)
        return Response({"token": raw, "expires_at": token.expires_at})


class LogoutView(APIView):
    @extend_schema(request=None, responses={204: None}, summary="Revoke the current token")
    def post(self, request: Request) -> Response:
        token: AuthToken = request.auth  # type: ignore[assignment]
        token.revoked_at = timezone.now()
        token.save(update_fields=["revoked_at"])
        record(action="auth.logout", outcome="success", actor_id=current_user(request).id)
        return Response(status=status.HTTP_204_NO_CONTENT)
