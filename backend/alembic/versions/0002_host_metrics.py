"""host_metrics table (agent metric ingestion)

Revision ID: 0002_host_metrics
Revises: 0001_initial
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_host_metrics"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "host_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "host_id",
            sa.Integer,
            sa.ForeignKey("hosts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cpu_percent", sa.Float),
        sa.Column("mem_percent", sa.Float),
        sa.Column("disk_percent", sa.Float),
        sa.Column("net_mbps", sa.Float),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_host_metrics_host_id", "host_metrics", ["host_id"])
    op.create_index("ix_host_metrics_collected_at", "host_metrics", ["collected_at"])


def downgrade() -> None:
    op.drop_table("host_metrics")
