"""SQL helpers used by migrations to apply tenant RLS to a table (ADR-0004)."""

from __future__ import annotations

APP_ROLE = "asg_app"

CREATE_ROLE_SQL = f"""
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
    CREATE ROLE {APP_ROLE} NOLOGIN NOSUPERUSER NOBYPASSRLS;
  END IF;
END $$;
GRANT {APP_ROLE} TO CURRENT_USER;
GRANT USAGE ON SCHEMA public TO {APP_ROLE};
"""

_TENANT_EXPR = "nullif(current_setting('app.tenant_id', true), '')::uuid"


def enable_rls_sql(
    table: str, column: str = "tenant_id", grants: str = "SELECT, INSERT, UPDATE, DELETE"
) -> str:
    return f"""
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON {table};
CREATE POLICY tenant_isolation ON {table}
  USING ({column} = {_TENANT_EXPR}) WITH CHECK ({column} = {_TENANT_EXPR});
GRANT {grants} ON {table} TO {APP_ROLE};
"""


def disable_rls_sql(table: str) -> str:
    return f"""
DROP POLICY IF EXISTS tenant_isolation ON {table};
ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
REVOKE ALL ON {table} FROM {APP_ROLE};
"""
