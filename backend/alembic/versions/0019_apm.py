"""Table apm_samples (APM applicatif).

Revision ID: 0019_apm
Revises: 0018_tickets
"""
import sqlalchemy as sa
from alembic import op

revision = "0019_apm"
down_revision = "0018_tickets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apm_samples",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("app_name", sa.String(128), nullable=False, index=True),
        sa.Column("environment", sa.String(64), nullable=False, server_default="prod"),
        sa.Column("requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float()),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("apm_samples")
