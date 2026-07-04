"""business services (BAM)

Revision ID: 0013_business_services
Revises: 0012_host_metrics_extra
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0013_business_services"
down_revision = "0012_host_metrics_extra"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "business_services",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("rule", sa.String(16), nullable=False, server_default="worst"),
        sa.Column("warning_threshold", sa.Float),
        sa.Column("critical_threshold", sa.Float),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "business_service_components",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("business_service_id", sa.Integer,
                  sa.ForeignKey("business_services.id", ondelete="CASCADE"), nullable=False),
        sa.Column("check_id", sa.Integer, sa.ForeignKey("checks.id", ondelete="CASCADE")),
        sa.Column("host_id", sa.Integer, sa.ForeignKey("hosts.id", ondelete="CASCADE")),
        sa.Column("label", sa.String(255)),
    )
    op.create_index("ix_bsc_service", "business_service_components", ["business_service_id"])


def downgrade() -> None:
    op.drop_table("business_service_components")
    op.drop_table("business_services")
