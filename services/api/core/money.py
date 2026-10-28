"""Money/quantity helpers. Rule (D-007): half-up to 2 dp, applied per line before summing."""

from __future__ import annotations

import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

TWO = Decimal("0.01")
FOUR = Decimal("0.0001")


def q2(x: Decimal | int | str) -> Decimal:
    return Decimal(x).quantize(TWO, rounding=ROUND_HALF_UP)


def q4(x: Decimal | int | str) -> Decimal:
    return Decimal(x).quantize(FOUR, rounding=ROUND_HALF_UP)


def request_hash(payload: Any) -> str:
    """Stable digest, so a replayed idempotency key with a different body is detected."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
