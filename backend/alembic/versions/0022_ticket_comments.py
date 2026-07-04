"""Table ticket_comments (suivis de tickets, façon GLPI).

Revision ID: 0022_ticket_comments
Revises: 0021_ticket_tasks
"""
import sqlalchemy as sa
from alembic import op

revision = "0022_ticket_comments"
down_revision = "0021_ticket_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticket_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("author", sa.String(255)),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_comments")
