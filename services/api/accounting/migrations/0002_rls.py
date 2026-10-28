"""RLS + invariants for accounting (ADR-0004). Generated pattern; reviewed by tests/test_domain_invariants.py."""

from django.db import migrations

from tenancy.rls import BALANCE_TRIGGER_SQL, enable_rls_sql, immutable_sql  # noqa: F401

FULL = [
    "accounting_account",
    "accounting_postingrule",
    "accounting_fiscalperiod",
    "accounting_documentsequence",
]
INSERT_ONLY = [
    "accounting_journalentry",
    "accounting_journalline",
]  # SELECT+INSERT (+UPDATE where listed in UPDATABLE)
IMMUTABLE = ["accounting_journalentry", "accounting_journalline"]

SQL = "".join(enable_rls_sql(t) for t in FULL)
SQL += "".join(enable_rls_sql(t, grants="SELECT, INSERT") for t in INSERT_ONLY)
SQL += "".join(immutable_sql(t) for t in IMMUTABLE)
SQL += BALANCE_TRIGGER_SQL


class Migration(migrations.Migration):
    dependencies = [("accounting", "0001_initial"), ("tenancy", "0002_rls")]
    operations = [migrations.RunSQL(SQL, migrations.RunSQL.noop)]
