"""Add measured decision/time ordering for filtered audit pages."""
from pathlib import Path
from alembic import op
revision='002'
down_revision='001'
branch_labels=None
depends_on=None

def upgrade():
    op.execute((Path(__file__).resolve().parents[2]/'indexes/008_audit_decision.sql').read_text())

def downgrade():
    op.execute('DROP INDEX ix_access_log_decision_time')
