"""Called by sales when an invoice is issued: creates the PENDING fiscal document if enabled."""

from __future__ import annotations

from typing import Any


def on_invoice_issued(invoice: Any) -> None:
    from fiscal.services import register_invoice

    register_invoice(invoice)
