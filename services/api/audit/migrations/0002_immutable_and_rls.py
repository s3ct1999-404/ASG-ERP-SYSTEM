"""Audit log is append-only (trigger, applies to every role) and tenant-isolated (RLS)."""

from django.db import migrations

from tenancy.rls import enable_rls_sql

TRIGGER = """
CREATE OR REPLACE FUNCTION audit_event_immutable() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'audit_event is append-only';
END $$ LANGUAGE plpgsql SET search_path = public;
DROP TRIGGER IF EXISTS audit_event_no_update ON audit_auditevent;
CREATE TRIGGER audit_event_no_update BEFORE UPDATE OR DELETE ON audit_auditevent
  FOR EACH ROW EXECUTE FUNCTION audit_event_immutable();
DROP TRIGGER IF EXISTS audit_event_no_truncate ON audit_auditevent;
CREATE TRIGGER audit_event_no_truncate BEFORE TRUNCATE ON audit_auditevent
  FOR EACH STATEMENT EXECUTE FUNCTION audit_event_immutable();
"""
UNDO = """
DROP TRIGGER IF EXISTS audit_event_no_update ON audit_auditevent;
DROP TRIGGER IF EXISTS audit_event_no_truncate ON audit_auditevent;
DROP FUNCTION IF EXISTS audit_event_immutable();
"""


class Migration(migrations.Migration):
    dependencies = [("audit", "0001_initial"), ("tenancy", "0002_rls")]
    operations = [
        migrations.RunSQL(TRIGGER, UNDO),
        migrations.RunSQL(
            enable_rls_sql("audit_auditevent", grants="SELECT, INSERT"),
            "DROP POLICY IF EXISTS tenant_isolation ON audit_auditevent;"
            "ALTER TABLE audit_auditevent DISABLE ROW LEVEL SECURITY;"
            "REVOKE ALL ON audit_auditevent FROM asg_app;",
        ),
    ]
