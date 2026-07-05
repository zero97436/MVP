"""Table knowledge_documents (base de connaissances RAG).

Revision ID: 0029_knowledge
Revises: 0028_multi_tenant
"""
import sqlalchemy as sa
from alembic import op

revision = "0029_knowledge"
down_revision = "0028_multi_tenant"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(255)),
        sa.Column("embedding", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("knowledge_documents")
