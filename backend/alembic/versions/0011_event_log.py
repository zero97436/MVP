"""global event log

Revision ID: 0011_event_log
Revises: 0010_maintenance
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_event_log"
down_revision = "0010_maintenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("type", sa.String(48), nullable=False),
        sa.Column("level", sa.String(16), nullable=False, server_default="info"),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("host_id", sa.Integer),
        sa.Column("check_id", sa.Integer),
        sa.Column("actor", sa.String(255)),
        sa.Column("meta", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_event_logs_type", "event_logs", ["type"])
    op.create_index("ix_event_logs_host_id", "event_logs", ["host_id"])
    op.create_index("ix_event_logs_check_id", "event_logs", ["check_id"])
    op.create_index("ix_event_logs_created_at", "event_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("event_logs")
