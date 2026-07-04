"""add executor_host_id to checks (agent probe / remote poller)

Revision ID: 0009_check_executor
Revises: 0008_agent_commands
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_check_executor"
down_revision = "0008_agent_commands"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "checks",
        sa.Column(
            "executor_host_id",
            sa.Integer,
            sa.ForeignKey("hosts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_checks_executor_host_id", "checks", ["executor_host_id"])


def downgrade() -> None:
    op.drop_index("ix_checks_executor_host_id", table_name="checks")
    op.drop_column("checks", "executor_host_id")
