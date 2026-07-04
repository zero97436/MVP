"""Table ticket_tasks (checklist dans les tickets).

Revision ID: 0021_ticket_tasks
Revises: 0020_dashboard_prefs
"""
import sqlalchemy as sa
from alembic import op

revision = "0021_ticket_tasks"
down_revision = "0020_dashboard_prefs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ticket_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id", ondelete="CASCADE"), index=True, nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_tasks")
