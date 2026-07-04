"""agent command queue (Level 2 remediation)

Revision ID: 0008_agent_commands
Revises: 0007_remediation_log
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_agent_commands"
down_revision = "0007_remediation_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_commands",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("host_id", sa.Integer, sa.ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("params", sa.JSON),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("result", sa.Text),
        sa.Column("requested_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_agent_commands_host_id", "agent_commands", ["host_id"])
    op.create_index("ix_agent_commands_status", "agent_commands", ["status"])


def downgrade() -> None:
    op.drop_table("agent_commands")
