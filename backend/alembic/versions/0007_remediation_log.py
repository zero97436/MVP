"""remediation audit log

Revision ID: 0007_remediation_log
Revises: 0006_host_metrics_hourly
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_remediation_log"
down_revision = "0006_host_metrics_hourly"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "remediation_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("alert_id", sa.Integer, sa.ForeignKey("alerts.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("detail", sa.Text),
        sa.Column("params", sa.JSON),
        sa.Column("performed_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_remediation_logs_alert_id", "remediation_logs", ["alert_id"])


def downgrade() -> None:
    op.drop_table("remediation_logs")
