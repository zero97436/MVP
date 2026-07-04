"""Ajoute category + icon aux services métier (Vue Opérations).

Revision ID: 0016_bam_category
Revises: 0015_host_dependency
"""
import sqlalchemy as sa
from alembic import op

revision = "0016_bam_category"
down_revision = "0015_host_dependency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "business_services",
        sa.Column("category", sa.String(64), nullable=False, server_default="Général"),
    )
    op.add_column("business_services", sa.Column("icon", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("business_services", "icon")
    op.drop_column("business_services", "category")
