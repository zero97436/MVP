"""Table tickets (ITSM / ticketing).

Revision ID: 0018_tickets
Revises: 0017_bam_position
"""
import sqlalchemy as sa
from alembic import op

revision = "0018_tickets"
down_revision = "0017_bam_position"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id", ondelete="SET NULL"), index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(16), nullable=False, server_default="open", index=True),
        sa.Column("priority", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("provider", sa.String(16), nullable=False, server_default="internal"),
        sa.Column("external_id", sa.String(128)),
        sa.Column("external_url", sa.String(512)),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tickets")
