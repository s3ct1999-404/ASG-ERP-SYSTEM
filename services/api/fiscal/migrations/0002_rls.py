"""RLS + append-only attempt log for fiscal tables."""

from django.db import migrations

from tenancy.rls import enable_rls_sql, immutable_sql

SQL = (
    enable_rls_sql("fiscal_fiscalsettings")
    + enable_rls_sql("fiscal_fiscaldocument")
    + enable_rls_sql("fiscal_fiscalattempt", grants="SELECT, INSERT")
    + immutable_sql("fiscal_fiscalattempt")
)


class Migration(migrations.Migration):
    dependencies = [("fiscal", "0001_initial"), ("tenancy", "0002_rls")]
    operations = [migrations.RunSQL(SQL, migrations.RunSQL.noop)]
