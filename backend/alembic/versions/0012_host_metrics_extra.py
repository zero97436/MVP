"""extend host_metrics: process_count, load1, temperature

Revision ID: 0012_host_metrics_extra
Revises: 0011_event_log
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0012_host_metrics_extra"
down_revision = "0011_event_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("host_metrics", sa.Column("process_count", sa.Integer, nullable=True))
    op.add_column("host_metrics", sa.Column("load1", sa.Float, nullable=True))
    op.add_column("host_metrics", sa.Column("temperature", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("host_metrics", "temperature")
    op.drop_column("host_metrics", "load1")
    op.drop_column("host_metrics", "process_count")
