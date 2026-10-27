"""Append-only audit log. A DB trigger (migration 0002) rejects UPDATE/DELETE for everyone."""

from __future__ import annotations

import uuid

from django.db import models


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Plain UUIDs (no FK) so history survives deactivation and cannot block deletions.
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    company_id = models.UUIDField(null=True, blank=True)
    branch_id = models.UUIDField(null=True, blank=True)
    actor_id = models.UUIDField(null=True, blank=True)
    action = models.CharField(max_length=100, db_index=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    outcome = models.CharField(max_length=20)  # success | denied | failed
    correlation_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
