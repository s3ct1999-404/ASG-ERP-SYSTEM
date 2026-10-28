"""RLS + invariants for masterdata (ADR-0004). Generated pattern; reviewed by tests/test_domain_invariants.py."""

from django.db import migrations

from tenancy.rls import BALANCE_TRIGGER_SQL, enable_rls_sql, immutable_sql  # noqa: F401

FULL = [
    "masterdata_unitofmeasure",
    "masterdata_taxcode",
    "masterdata_partner",
    "masterdata_product",
    "masterdata_warehouse",
]
INSERT_ONLY: list[str] = []  # SELECT+INSERT (+UPDATE where listed in UPDATABLE)
IMMUTABLE: list[str] = []

SQL = "".join(enable_rls_sql(t) for t in FULL)
SQL += "".join(enable_rls_sql(t, grants="SELECT, INSERT") for t in INSERT_ONLY)
SQL += "".join(immutable_sql(t) for t in IMMUTABLE)


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0001_initial"),
        ("tenancy", "0002_rls"),
        ("identity", "0002_rls_lockdown"),
    ]
    operations = [migrations.RunSQL(SQL, migrations.RunSQL.noop)]
