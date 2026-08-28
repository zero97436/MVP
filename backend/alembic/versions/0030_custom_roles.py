"""Rôles personnalisés (RBAC par section) + élargissement de users.role.

Revision ID: 0030_custom_roles
Revises: 0029_knowledge
"""
import sqlalchemy as sa
from alembic import op

revision = "0030_custom_roles"
down_revision = "0029_knowledge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(255)),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    # Élargit users.role (16 -> 64) pour accueillir les noms de rôles personnalisés.
    with op.batch_alter_table("users") as batch:
        batch.alter_column("role", type_=sa.String(64))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.alter_column("role", type_=sa.String(16))
    op.drop_table("roles")
