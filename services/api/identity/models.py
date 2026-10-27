"""Global identity (ADR-0003/0004): a User may belong to several tenants via Membership."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import timedelta
from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

TOKEN_TTL = timedelta(hours=12)


class UserManager(BaseUserManager["User"]):
    use_in_migrations = True

    def create_user(self, email: str, password: str | None, **extra: Any) -> User:
        if not email:
            raise ValueError("email is required")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    # Platform operators may provision tenants; they get NO tenant data access (D-021).
    is_platform_operator = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # type: ignore[misc]

    def __str__(self) -> str:
        return self.email


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class AuthToken(models.Model):
    """Bearer token. Only the SHA-256 digest is stored; the raw value is shown once."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tokens")
    key_hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def issue(cls, user: User) -> tuple[AuthToken, str]:
        raw = secrets.token_urlsafe(40)
        token = cls.objects.create(
            user=user, key_hash=hash_token(raw), expires_at=timezone.now() + TOKEN_TTL
        )
        return token, raw

    @property
    def is_valid(self) -> bool:
        return self.revoked_at is None and self.expires_at > timezone.now()
