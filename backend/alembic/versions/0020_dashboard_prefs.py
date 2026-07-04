"""Table dashboard_prefs (dashboards personnalisables par utilisateur).

Revision ID: 0020_dashboard_prefs
Revises: 0019_apm
"""
import sqlalchemy as sa
from alembic import op

revision = "0020_dashboard_prefs"
down_revision = "0019_apm"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dashboard_prefs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False),
        sa.Column("layout", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("dashboard_prefs")
