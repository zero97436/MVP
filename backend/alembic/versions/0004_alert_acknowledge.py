"""add acknowledgement fields to alerts

Revision ID: 0004_alert_acknowledge
Revises: 0003_host_metrics_disks
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_alert_acknowledge"
down_revision = "0003_host_metrics_disks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alerts",
        sa.Column("acknowledged", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.add_column("alerts", sa.Column("acknowledged_by", sa.String(255), nullable=True))
    op.add_column(
        "alerts", sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index("ix_alerts_acknowledged", "alerts", ["acknowledged"])


def downgrade() -> None:
    op.drop_index("ix_alerts_acknowledged", table_name="alerts")
    op.drop_column("alerts", "acknowledged_at")
    op.drop_column("alerts", "acknowledged_by")
    op.drop_column("alerts", "acknowledged")
