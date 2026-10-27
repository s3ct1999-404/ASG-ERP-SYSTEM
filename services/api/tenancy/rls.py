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
-- Supabase auto-grants new tables to its REST roles; this service never uses them.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
  END IF;
END $$;
"""


def revoke_rest_roles_sql(table: str) -> str:
    return f"""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    REVOKE ALL ON TABLE {table} FROM anon, authenticated;
  END IF;
END $$;
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
{revoke_rest_roles_sql(table)}"""


def disable_rls_sql(table: str) -> str:
    return f"""
DROP POLICY IF EXISTS tenant_isolation ON {table};
ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
REVOKE ALL ON {table} FROM {APP_ROLE};
"""


def immutable_sql(table: str) -> str:
    """Reject UPDATE/DELETE/TRUNCATE on ``table`` for every role (append-only ledgers)."""
    return f"""
CREATE OR REPLACE FUNCTION asg_immutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
END $$ LANGUAGE plpgsql SET search_path = public;
DROP TRIGGER IF EXISTS {table}_immutable ON {table};
CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table}
  FOR EACH ROW EXECUTE FUNCTION asg_immutable();
DROP TRIGGER IF EXISTS {table}_no_truncate ON {table};
CREATE TRIGGER {table}_no_truncate BEFORE TRUNCATE ON {table}
  FOR EACH STATEMENT EXECUTE FUNCTION asg_immutable();
"""


BALANCE_TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION asg_journal_balanced() RETURNS trigger AS $$
DECLARE diff numeric;
BEGIN
  SELECT coalesce(sum(debit),0) - coalesce(sum(credit),0) INTO diff
    FROM accounting_journalline WHERE entry_id = NEW.entry_id;
  IF diff <> 0 THEN
    RAISE EXCEPTION 'journal entry % is unbalanced by %', NEW.entry_id, diff;
  END IF;
  RETURN NULL;
END $$ LANGUAGE plpgsql SET search_path = public;
DROP TRIGGER IF EXISTS journalline_balanced ON accounting_journalline;
CREATE CONSTRAINT TRIGGER journalline_balanced AFTER INSERT ON accounting_journalline
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION asg_journal_balanced();
"""
