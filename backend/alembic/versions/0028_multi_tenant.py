"""Multi-tenant : table tenants + tenant_id sur users et hosts.

Revision ID: 0028_multi_tenant
Revises: 0027_audit_log
"""
import sqlalchemy as sa
from alembic import op

revision = "0028_multi_tenant"
down_revision = "0027_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column("users", sa.Column("tenant_id", sa.Integer(),
                  sa.ForeignKey("tenants.id", ondelete="SET NULL"), index=True))
    op.add_column("hosts", sa.Column("tenant_id", sa.Integer(),
                  sa.ForeignKey("tenants.id", ondelete="SET NULL"), index=True))


def downgrade() -> None:
    op.drop_column("hosts", "tenant_id")
    op.drop_column("users", "tenant_id")
    op.drop_table("tenants")
