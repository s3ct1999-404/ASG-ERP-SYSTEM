"""Base class for every tenant-scoped API view: auth -> membership -> permission -> RLS mode."""

from __future__ import annotations

import uuid
from typing import Any, ClassVar

from django.core.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.service import record
from identity.authentication import current_user
from tenancy.context import AccessContext, build_access, enter_tenant, leave_tenant

TENANT_HEADER = "X-Tenant-ID"


class TenantAPIView(APIView):
    """Subclasses MUST declare ``permission_map`` (HTTP method -> permission code).

    A method with no entry is denied. Object-level scope checks are the view/service's job via
    ``request.access`` (see ``tenancy.context.AccessContext``).
    """

    permission_map: ClassVar[dict[str, str]] = {}
    access: AccessContext

    def initial(self, request: Request, *args: Any, **kwargs: Any) -> None:
        super().initial(request, *args, **kwargs)  # authentication, throttling
        raw = request.headers.get(TENANT_HEADER, "")
        try:
            tenant_id = uuid.UUID(raw)
        except ValueError:
            raise PermissionDenied("A valid X-Tenant-ID header is required.") from None
        self.access = build_access(current_user(request).id, tenant_id)
        perm = self.permission_map.get(request.method or "")
        if perm is None or not self.access.has_any(perm):
            record(
                action="authz.denied",
                outcome="denied",
                tenant_id=tenant_id,
                durable=True,
                actor_id=current_user(request).id,
                metadata={"permission": perm, "path": request.path},
            )
            raise PermissionDenied("Not permitted.")
        enter_tenant(tenant_id)

    def finalize_response(
        self, request: Request, response: Response, *args: Any, **kwargs: Any
    ) -> Response:
        leave_tenant()
        return super().finalize_response(request, response, *args, **kwargs)
