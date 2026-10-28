"""RLS + invariants for sales (ADR-0004). Generated pattern; reviewed by tests/test_domain_invariants.py."""

from django.db import migrations

from tenancy.rls import BALANCE_TRIGGER_SQL, enable_rls_sql, immutable_sql  # noqa: F401

FULL = ["sales_salesinvoice"]
INSERT_ONLY = [
    "sales_invoiceline",
    "sales_payment",
]  # SELECT+INSERT (+UPDATE where listed in UPDATABLE)
IMMUTABLE = ["sales_invoiceline", "sales_payment"]

SQL = "".join(enable_rls_sql(t) for t in FULL)
SQL += "".join(enable_rls_sql(t, grants="SELECT, INSERT") for t in INSERT_ONLY)
SQL += "".join(immutable_sql(t) for t in IMMUTABLE)


class Migration(migrations.Migration):
    dependencies = [("sales", "0001_initial"), ("tenancy", "0002_rls")]
    operations = [migrations.RunSQL(SQL, migrations.RunSQL.noop)]
