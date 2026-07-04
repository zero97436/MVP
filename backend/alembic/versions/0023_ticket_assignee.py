"""Assignation des tickets à un utilisateur.

Revision ID: 0023_ticket_assignee
Revises: 0022_ticket_comments
"""
import sqlalchemy as sa
from alembic import op

revision = "0023_ticket_assignee"
down_revision = "0022_ticket_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tickets",
        sa.Column("assigned_to_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), index=True),
    )


def downgrade() -> None:
    op.drop_column("tickets", "assigned_to_id")
