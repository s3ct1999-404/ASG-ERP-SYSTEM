from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any, ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from accounting import services
from accounting.models import Account, JournalEntry
from tenancy.base import TenantAPIView
from tenancy.models import Company


class LineIn(serializers.Serializer[dict[str, Any]]):
    account = serializers.UUIDField()
    debit = serializers.DecimalField(max_digits=20, decimal_places=2, default=Decimal(0))
    credit = serializers.DecimalField(max_digits=20, decimal_places=2, default=Decimal(0))


class JournalIn(serializers.Serializer[dict[str, Any]]):
    company = serializers.UUIDField()
    date = serializers.DateField()
    memo = serializers.CharField(max_length=300)
    lines = LineIn(many=True)


class ReverseIn(serializers.Serializer[dict[str, Any]]):
    date = serializers.DateField(default=dt.date.today)
    reason = serializers.CharField(max_length=200)


class PeriodIn(serializers.Serializer[dict[str, Any]]):
    company = serializers.UUIDField()
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)
    status = serializers.ChoiceField(choices=["open", "closed"])


class AccountListView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "accounting.read"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(Account.objects.all(), "accounting.read", "company_id", None)
        return Response(
            [
                {
                    "id": a.id,
                    "company": a.company_id,
                    "code": a.code,
                    "name": a.name,
                    "type": a.type,
                    "requires_review": a.requires_review,
                }
                for a in qs.order_by("code")
            ]
        )


class JournalView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "accounting.read", "POST": "accounting.post"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(
            JournalEntry.objects.prefetch_related("lines__account"),
            "accounting.read",
            "company_id",
            None,
        )
        return Response(
            [
                {
                    "id": e.id,
                    "number": e.number,
                    "date": e.date,
                    "memo": e.memo,
                    "source": e.source_type,
                    "lines": [
                        {"account": ln.account.code, "debit": ln.debit, "credit": ln.credit}
                        for ln in e.lines.all()
                    ],
                }
                for e in qs.order_by("-created_at")[:100]
            ]
        )

    @extend_schema(request=JournalIn, responses={201: None})
    def post(self, request: Request) -> Response:
        s = JournalIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        e = services.post_manual(
            self.access,
            company_id=d["company"],
            date=d["date"],
            memo=d["memo"],
            lines=[dict(ln) for ln in d["lines"]],
        )
        return Response({"id": e.id, "number": e.number}, status=201)


class ReverseView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "accounting.reverse"}

    @extend_schema(request=ReverseIn, responses={201: None})
    def post(self, request: Request, entry_id: Any) -> Response:
        s = ReverseIn(data=request.data)
        s.is_valid(raise_exception=True)
        e = services.reverse_entry(self.access, entry_id=entry_id, **s.validated_data)
        return Response({"id": e.id, "number": e.number}, status=201)


class PeriodView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "accounting.manage_periods"}

    @extend_schema(request=PeriodIn, responses={200: None})
    def post(self, request: Request) -> Response:
        s = PeriodIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        p = services.set_period_status(
            self.access,
            company_id=d["company"],
            year=d["year"],
            month=d["month"],
            status=d["status"],
        )
        return Response({"year": p.year, "month": p.month, "status": p.status})


class ReportView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "accounting.read"}

    @extend_schema(responses={200: None})
    def get(self, request: Request, company_id: Any, report: str) -> Response:
        self.access.require("accounting.read", company_id)
        if not Company.objects.filter(id=company_id).exists():
            return Response(status=404)
        if report == "trial-balance":
            return Response(services.trial_balance(company_id))
        return Response(services.statements(company_id))
