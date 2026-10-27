from __future__ import annotations

from typing import cast

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.request import Request

from identity.models import AuthToken, User, hash_token


def current_user(request: Request) -> User:
    """The authenticated user (views using this are behind IsAuthenticated)."""
    return cast(User, request.user)


class BearerTokenAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(self, request: Request) -> tuple[User, AuthToken] | None:
        parts = get_authorization_header(request).split()
        if not parts or parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed("Invalid token header.")
        try:
            token = AuthToken.objects.select_related("user").get(
                key_hash=hash_token(parts[1].decode())
            )
        except (AuthToken.DoesNotExist, UnicodeError):
            raise exceptions.AuthenticationFailed("Invalid token.") from None
        if not token.is_valid or not token.user.is_active:
            raise exceptions.AuthenticationFailed("Invalid or expired token.")
        return token.user, token

    def authenticate_header(self, request: Request) -> str:
        return "Bearer"
