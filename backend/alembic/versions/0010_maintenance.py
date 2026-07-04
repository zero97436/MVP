"""maintenance windows (planned downtime)

Revision ID: 0010_maintenance
Revises: 0009_check_executor
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0010_maintenance"
down_revision = "0009_check_executor"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_windows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("host_id", sa.Integer, sa.ForeignKey("hosts.id", ondelete="CASCADE")),
        sa.Column("check_id", sa.Integer, sa.ForeignKey("checks.id", ondelete="CASCADE")),
        sa.Column("reason", sa.Text),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_maintenance_windows_host_id", "maintenance_windows", ["host_id"])
    op.create_index("ix_maintenance_windows_check_id", "maintenance_windows", ["check_id"])
    op.create_index("ix_maintenance_windows_ends_at", "maintenance_windows", ["ends_at"])


def downgrade() -> None:
    op.drop_table("maintenance_windows")
