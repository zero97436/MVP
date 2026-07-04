"""add role to users (RBAC)

Revision ID: 0005_user_role
Revises: 0004_alert_acknowledge
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_user_role"
down_revision = "0004_alert_acknowledge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(16), nullable=False, server_default="viewer"),
    )
    # Aligne le rôle sur l'ancien flag is_admin.
    op.execute("UPDATE users SET role = 'admin' WHERE is_admin = true")


def downgrade() -> None:
    op.drop_column("users", "role")
