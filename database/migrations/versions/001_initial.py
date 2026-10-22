"""Eight-table SQL baseline with controlled authorization routines."""
from pathlib import Path
from alembic import op
revision='001'
down_revision=None
branch_labels=None
depends_on=None

FILES = ['schema/000_roles.sql','schema/001_core_schema.sql','schema/002_views.sql',
         'functions/003_authorization.sql','procedures/004_policy.sql',
         'functions/005_management.sql','cursors/006_activity_summary.sql','schema/007_privileges.sql']

def upgrade():
    root=Path(__file__).resolve().parents[2]
    for path in FILES:
        op.get_bind().exec_driver_sql((root/path).read_text(), execution_options={"no_parameters": True})

def downgrade():
    raise RuntimeError('Destructive downgrades disabled; recreate only disposable databases')
