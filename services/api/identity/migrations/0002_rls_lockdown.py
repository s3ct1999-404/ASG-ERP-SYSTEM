"""Identity tables: RLS on, no REST-role access. Only the owner role (system mode) reads
passwords/tokens. The app role may read non-secret columns of users who are members of the
*current* tenant (policy joins through RLS-protected membership)."""

from django.db import migrations

from tenancy.rls import revoke_rest_roles_sql

FWD = (
    """
ALTER TABLE identity_user ENABLE ROW LEVEL SECURITY;
ALTER TABLE identity_authtoken ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS member_read ON identity_user;
CREATE POLICY member_read ON identity_user FOR SELECT TO asg_app
  USING (id IN (SELECT user_id FROM tenancy_membership));
"""
    + revoke_rest_roles_sql("identity_user")
    + revoke_rest_roles_sql("identity_authtoken")
)

REV = """
DROP POLICY IF EXISTS member_read ON identity_user;
ALTER TABLE identity_user DISABLE ROW LEVEL SECURITY;
ALTER TABLE identity_authtoken DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [("identity", "0001_initial"), ("tenancy", "0002_rls")]
    operations = [migrations.RunSQL(FWD, REV)]
