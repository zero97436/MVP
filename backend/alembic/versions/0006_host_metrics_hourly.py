"""hourly rollup table for host metrics (downsampling)

Revision ID: 0006_host_metrics_hourly
Revises: 0005_user_role
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_host_metrics_hourly"
down_revision = "0005_user_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "host_metrics_hourly",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "host_id",
            sa.Integer,
            sa.ForeignKey("hosts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bucket", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cpu_avg", sa.Float),
        sa.Column("cpu_max", sa.Float),
        sa.Column("mem_avg", sa.Float),
        sa.Column("mem_max", sa.Float),
        sa.Column("disk_avg", sa.Float),
        sa.Column("disk_max", sa.Float),
        sa.Column("net_avg", sa.Float),
        sa.Column("net_max", sa.Float),
        sa.Column("sample_count", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_host_metrics_hourly_host_id", "host_metrics_hourly", ["host_id"])
    op.create_index("ix_host_metrics_hourly_bucket", "host_metrics_hourly", ["bucket"])
    op.create_index(
        "uq_host_metrics_hourly_host_bucket",
        "host_metrics_hourly",
        ["host_id", "bucket"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("host_metrics_hourly")
