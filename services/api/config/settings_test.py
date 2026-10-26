"""Settings used by the test suite only. Never use outside tests."""

import os

os.environ.setdefault("SECRET_KEY", "test-only-not-a-secret")

from config.settings import *  # noqa: E402,F401,F403
