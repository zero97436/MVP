"""add per-disk breakdown to host_metrics

Revision ID: 0003_host_metrics_disks
Revises: 0002_host_metrics
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_host_metrics_disks"
down_revision = "0002_host_metrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("host_metrics", sa.Column("disks", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("host_metrics", "disks")
