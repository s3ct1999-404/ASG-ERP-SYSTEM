"""Fail-closed configuration and deny-by-default API behaviour."""

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

API_ROOT = Path(__file__).resolve().parent.parent


def _run_settings_probe(
    env_overrides: dict[str, str], remove: tuple[str, ...] = ()
) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in remove}
    env.update(env_overrides)
    env["PYTHONPATH"] = str(API_ROOT)
    code = "import config.settings as s; print(f'DEBUG={s.DEBUG};HOSTS={s.ALLOWED_HOSTS}')"
    return subprocess.run(  # noqa: S603
        [sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False
    )


def test_settings_refuse_to_load_without_secret_key() -> None:
    result = _run_settings_probe({}, remove=("SECRET_KEY",))
    assert result.returncode != 0
    assert "SECRET_KEY" in result.stderr


def test_debug_and_allowed_hosts_fail_closed_by_default() -> None:
    result = _run_settings_probe({"SECRET_KEY": "x" * 20}, remove=("DEBUG", "ALLOWED_HOSTS"))
    assert result.returncode == 0, result.stderr
    assert "DEBUG=False" in result.stdout
    assert "HOSTS=[]" in result.stdout


def test_drf_default_permission_is_authenticated() -> None:
    assert settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == [
        "rest_framework.permissions.IsAuthenticated"
    ]


def test_view_without_explicit_permissions_is_denied() -> None:
    class Unprotected(APIView):
        """A view that forgot to declare permissions must still be denied."""

        def get(self, request: object) -> Response:
            return Response({"secret": "data"})

    request = APIRequestFactory().get("/anything")
    response = Unprotected.as_view()(request)
    assert response.status_code in (401, 403)
    assert b"secret" not in response.rendered_content
    assert IsAuthenticated in [type(p) for p in Unprotected().get_permissions()]
