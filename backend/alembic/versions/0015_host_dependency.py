"""host dependency (parent_host_id)

Revision ID: 0015_host_dependency
Revises: 0014_escalation
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0015_host_dependency"
down_revision = "0014_escalation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "hosts",
        sa.Column("parent_host_id", sa.Integer, sa.ForeignKey("hosts.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_hosts_parent_host_id", "hosts", ["parent_host_id"])


def downgrade() -> None:
    op.drop_index("ix_hosts_parent_host_id", table_name="hosts")
    op.drop_column("hosts", "parent_host_id")
