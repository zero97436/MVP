"""alert escalation + channel escalation_only / active_hours

Revision ID: 0014_escalation
Revises: 0013_business_services
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0014_escalation"
down_revision = "0013_business_services"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notification_channels",
                  sa.Column("escalation_only", sa.Boolean, nullable=False, server_default=sa.false()))
    op.add_column("notification_channels", sa.Column("active_hours", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("notification_channels", "active_hours")
    op.drop_column("notification_channels", "escalation_only")
    op.drop_column("alerts", "escalated_at")
