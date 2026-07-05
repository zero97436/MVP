"""Table branding (personnalisation de marque — plan Professional).

Revision ID: 0026_branding
Revises: 0025_host_geo
"""
import sqlalchemy as sa
from alembic import op

revision = "0026_branding"
down_revision = "0025_host_geo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branding",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("display_name", sa.String(64)),
        sa.Column("tagline", sa.String(128)),
        sa.Column("logo_url", sa.Text()),
        sa.Column("accent_color", sa.String(16)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("branding")
