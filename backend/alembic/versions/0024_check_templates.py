"""Table check_templates (modèles de checks).

Revision ID: 0024_check_templates
Revises: 0023_ticket_assignee
"""
import sqlalchemy as sa
from alembic import op

revision = "0024_check_templates"
down_revision = "0023_ticket_assignee"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "check_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("check_templates")
