"""Django settings for the ASG ERP API.

Every environment-specific value comes from environment variables (see the
repository's `.env.example`). Defaults fail closed: no default SECRET_KEY,
DEBUG is off, ALLOWED_HOSTS is empty.

Deliberately NOT installed yet: ``django.contrib.auth`` / sessions / contenttypes.
Django's user model must be chosen before the first migration and belongs to the
identity-access design (ASG-005/ASG-006). Until then the API has no
authentication, and the DRF defaults below deny every request that does not
explicitly opt in (see ``core.views``).
"""

from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "The SECRET_KEY environment variable is required. "
        "Copy .env.example to .env and set a unique value; never commit it."
    )

DEBUG = _env_bool("DEBUG", False)
ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "rest_framework",
    "drf_spectacular",
    "core",
    "identity",
    "tenancy",
    "audit",
    "masterdata",
    "inventory",
    "accounting",
    "sales",
    "fiscal",
]

# Custom user model, fixed BEFORE the first migration (ADR-0004). django.contrib.auth is
# deliberately NOT installed: authorisation is our own tenant-scoped RBAC (tenancy app).
AUTH_USER_MODEL = "identity.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = []

MIDDLEWARE = [
    "config.middleware.RequestIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "asg_erp"),
        "USER": os.environ.get("DB_USER", "asg"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {"sslmode": os.environ.get("DB_SSLMODE", "prefer")},
    }
}
# Durable audit connection: same database, autocommit, NOT wrapped in the request transaction,
# so denial/failure events survive the rollback that DRF performs on 4xx/5xx responses.
DATABASES["audit"] = {
    **DATABASES["default"],
    "ATOMIC_REQUESTS": False,
    "TEST": {"MIRROR": "default"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True
TIME_ZONE = "UTC"

# --- Transport / cookie hardening -------------------------------------------
# TLS termination and proxy topology are a deployment decision (assumption A-002,
# not yet an ADR), so redirect/HSTS are env-controlled and OFF by default.
# TODO(deployment ADR): decide SECURE_PROXY_SSL_HEADER and enable these in production.
SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# --- Django REST Framework: deny by default ---------------------------------
REST_FRAMEWORK = {
    # No authentication scheme exists yet (ASG-006). With no authenticators and
    # UNAUTHENTICATED_USER=None, request.user is None, so IsAuthenticated denies.
    "DEFAULT_AUTHENTICATION_CLASSES": ["identity.authentication.BearerTokenAuthentication"],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {"login": os.environ.get("LOGIN_THROTTLE", "10/min")},
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ASG ERP API",
    "DESCRIPTION": "Versioned REST API for ASG ERP. Contract-first: see docs/api/openapi.yaml.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- Structured logging ------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "config.logging_utils.RequestIdFilter"}},
    "formatters": {"json": {"()": "config.logging_utils.JsonFormatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["request_id"],
        }
    },
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
