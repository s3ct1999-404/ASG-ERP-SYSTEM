"""Settings used by the test suite only. Never use outside tests."""

import os

os.environ.setdefault("SECRET_KEY", "test-only-not-a-secret")

from config.settings import *  # noqa: E402,F401,F403

# Tests log in many times; the throttle itself is covered by tests/test_throttle.py.
REST_FRAMEWORK = {**REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {"login": "100000/min"}}  # noqa: F405
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
