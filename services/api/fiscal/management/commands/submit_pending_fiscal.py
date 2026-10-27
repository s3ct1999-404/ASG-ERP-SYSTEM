"""Worker entry point: submit due PENDING/FAILED_RETRYABLE fiscal documents for every tenant.

Run on a schedule (e.g. every minute). Safe to run concurrently: documents are row-locked and a
finished document is never resubmitted."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from fiscal.models import FiscalDocument
from fiscal.services import submit_document
from tenancy.context import tenant_mode
from tenancy.models import Tenant


class Command(BaseCommand):
    help = "Submit due fiscal documents."

    def handle(self, *args: Any, **opts: Any) -> None:
        sent = 0
        for tid in Tenant.objects.filter(status="active").values_list("id", flat=True):
            with tenant_mode(tid):
                due = list(
                    FiscalDocument.objects.filter(
                        Q(status="PENDING_FISCALISATION")
                        | Q(status="FAILED_RETRYABLE", next_attempt_at__lte=timezone.now())
                    ).values_list("id", flat=True)[:100]
                )
            for doc_id in due:
                with tenant_mode(tid):
                    submit_document(None, doc_id=doc_id, actor_id=None)
                    sent += 1
        self.stdout.write(f"processed {sent} document(s)")
