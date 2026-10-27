"""RLS + invariants for inventory (ADR-0004). Generated pattern; reviewed by tests/test_domain_invariants.py."""

from django.db import migrations

from tenancy.rls import BALANCE_TRIGGER_SQL, enable_rls_sql, immutable_sql  # noqa: F401

FULL = ["inventory_stockbalance"]
INSERT_ONLY = ["inventory_stockmovement"]  # SELECT+INSERT (+UPDATE where listed in UPDATABLE)
IMMUTABLE = ["inventory_stockmovement"]

SQL = "".join(enable_rls_sql(t) for t in FULL)
SQL += "".join(enable_rls_sql(t, grants="SELECT, INSERT") for t in INSERT_ONLY)
SQL += "".join(immutable_sql(t) for t in IMMUTABLE)


class Migration(migrations.Migration):
    dependencies = [("inventory", "0002_initial"), ("tenancy", "0002_rls")]
    operations = [migrations.RunSQL(SQL, migrations.RunSQL.noop)]
