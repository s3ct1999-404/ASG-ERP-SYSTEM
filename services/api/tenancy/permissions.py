"""Permission registry and system role templates. Codes are the only authorisation vocabulary."""

from __future__ import annotations

PERMISSIONS: dict[str, str] = {
    "tenancy.read": "View companies, branches, members",
    "tenancy.manage_org": "Create/edit companies and branches",
    "tenancy.manage_access": "Manage members, roles and assignments",
    "audit.read": "View the audit trail",
    "apps.manage": "Install/enable/disable/uninstall apps",
    "apps.read": "View the app catalogue and installations",
    "masterdata.read": "View customers, suppliers, products, warehouses, tax codes",
    "masterdata.write": "Create/edit master data",
    "inventory.read": "View stock and movements",
    "inventory.receive": "Receive stock",
    "inventory.adjust": "Adjust stock",
    "inventory.transfer": "Transfer stock between warehouses",
    "sales.read": "View quotations, orders, invoices",
    "sales.write": "Create/edit quotations and orders",
    "sales.confirm": "Confirm orders and issue invoices",
    "pos.sell": "Operate a POS till and record sales",
    "pos.manage_sessions": "Open/close/reconcile till sessions",
    "payments.record": "Record customer/supplier payments",
    "accounting.read": "View ledgers, journals and statements",
    "accounting.post": "Post journal entries",
    "accounting.reverse": "Reverse posted entries",
    "accounting.manage_periods": "Close/reopen fiscal periods; manage chart of accounts",
    "fiscal.read": "View fiscal (EFRIS) document status",
    "fiscal.submit": "Submit/retry fiscal documents",
    "fiscal.manage": "Configure fiscal provider settings",
    "reports.read": "View reports and dashboards",
    "hr.read": "View employee records",
    "hr.write": "Manage employee records",
    "projects.read": "View projects and tasks",
    "projects.write": "Manage projects and tasks",
    "documents.read": "View documents",
    "documents.write": "Upload/edit documents",
    "documents.approve": "Approve documents/workflow steps",
    "fleet.read": "View vehicles, trips, maintenance",
    "fleet.write": "Manage vehicles, trips, maintenance",
    "notifications.read": "View own notifications",
    "sync.submit": "Submit offline operations",
}

_READ = [p for p in PERMISSIONS if p.endswith(".read")]

SYSTEM_ROLES: dict[str, list[str]] = {
    "Owner": sorted(PERMISSIONS),
    "Branch Manager": sorted(
        p
        for p in PERMISSIONS
        if p
        not in {
            "tenancy.manage_org",
            "tenancy.manage_access",
            "apps.manage",
            "accounting.manage_periods",
            "fiscal.manage",
        }
    ),
    "Cashier": [
        "pos.sell",
        "payments.record",
        "masterdata.read",
        "inventory.read",
        "sales.read",
        "sync.submit",
        "notifications.read",
        "fiscal.read",
    ],
    "Storekeeper": [
        "inventory.read",
        "inventory.receive",
        "inventory.adjust",
        "inventory.transfer",
        "masterdata.read",
        "masterdata.write",
        "sync.submit",
        "notifications.read",
    ],
    "Accountant": [
        "accounting.read",
        "accounting.post",
        "accounting.reverse",
        "accounting.manage_periods",
        "sales.read",
        "reports.read",
        "masterdata.read",
        "payments.record",
        "fiscal.read",
        "audit.read",
        "notifications.read",
    ],
    "Viewer": sorted(set(_READ)),
}
