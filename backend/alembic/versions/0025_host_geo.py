"""Localisation des hôtes (site + lat/lon) pour la vue géographique.

Revision ID: 0025_host_geo
Revises: 0024_check_templates
"""
import sqlalchemy as sa
from alembic import op

revision = "0025_host_geo"
down_revision = "0024_check_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("hosts", sa.Column("location", sa.String(255), nullable=True))
    op.add_column("hosts", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("hosts", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("hosts", "longitude")
    op.drop_column("hosts", "latitude")
    op.drop_column("hosts", "location")
