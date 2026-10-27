"""App role + row-level security for tenancy tables (ADR-0004)."""

from django.db import migrations

from tenancy.rls import CREATE_ROLE_SQL, disable_rls_sql, enable_rls_sql

TENANT_OWNED = ["company", "branch", "role", "membership", "roleassignment"]
USER_COLUMNS_GRANT = "GRANT SELECT (id, email, full_name, is_active) ON identity_user TO asg_app;"


def _fwd() -> list[str]:
    sql = [CREATE_ROLE_SQL]
    sql += [enable_rls_sql(f"tenancy_{t}") for t in TENANT_OWNED]
    sql.append(enable_rls_sql("tenancy_tenant", column="id", grants="SELECT"))
    sql.append(USER_COLUMNS_GRANT)
    return sql


def _rev() -> list[str]:
    sql = [disable_rls_sql(f"tenancy_{t}") for t in TENANT_OWNED] + [
        disable_rls_sql("tenancy_tenant")
    ]
    sql.append("REVOKE ALL ON identity_user FROM asg_app;")
    return sql


class Migration(migrations.Migration):
    dependencies = [("tenancy", "0001_initial"), ("identity", "0001_initial")]
    operations = [migrations.RunSQL("\n".join(_fwd()), "\n".join(_rev()))]
