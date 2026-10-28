from __future__ import annotations

from django.core.cache import cache
from rest_framework.test import APIClient

from identity.views import LoginThrottle


def test_login_is_rate_limited(db: object, monkeypatch: object) -> None:
    cache.clear()
    monkeypatch.setattr(LoginThrottle, "THROTTLE_RATES", {"login": "3/min"})
    c = APIClient()
    codes = [
        c.post(
            "/api/v1/auth/login/", {"email": "a@b.test", "password": "x"}, format="json"
        ).status_code
        for _ in range(5)
    ]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]
    cache.clear()
