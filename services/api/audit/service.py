"""Write audit events. Secrets/PII-bearing keys are redacted before storage (Blueprint §6.4)."""

from __future__ import annotations

import re
from typing import Any

from audit.models import AuditEvent
from config.logging_utils import current_request_id

_SENSITIVE = re.compile(r"pass(word)?|token|secret|authorization|api[_-]?key|credential|card", re.I)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ("[REDACTED]" if _SENSITIVE.search(str(k)) else redact(v)) for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def record(
    *,
    action: str,
    outcome: str = "success",
    tenant_id: Any = None,
    company_id: Any = None,
    branch_id: Any = None,
    actor_id: Any = None,
    object_type: str = "",
    object_id: Any = "",
    metadata: dict[str, Any] | None = None,
    durable: bool = False,
) -> AuditEvent:
    """``durable=True`` writes on the separate autocommit connection: use it for denials and
    failures, which happen inside requests that are rolled back. Successful business events are
    written in the same transaction as the change they describe (atomic with it)."""
    manager = AuditEvent.objects.using("audit") if durable else AuditEvent.objects
    return manager.create(
        tenant_id=tenant_id,
        company_id=company_id,
        branch_id=branch_id,
        actor_id=actor_id,
        action=action,
        object_type=object_type,
        object_id=str(object_id or ""),
        outcome=outcome,
        correlation_id=current_request_id() or "",
        metadata=redact(metadata or {}),
    )
