"""Ajoute pos_x / pos_y aux services métier (carte drag & drop).

Revision ID: 0017_bam_position
Revises: 0016_bam_category
"""
import sqlalchemy as sa
from alembic import op

revision = "0017_bam_position"
down_revision = "0016_bam_category"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("business_services", sa.Column("pos_x", sa.Integer(), nullable=True))
    op.add_column("business_services", sa.Column("pos_y", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("business_services", "pos_y")
    op.drop_column("business_services", "pos_x")
