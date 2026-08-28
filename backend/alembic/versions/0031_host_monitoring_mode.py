"""Mode de supervision par hôte (agentless / agent / ssh) + config SSH.

Revision ID: 0031_host_monitoring_mode
Revises: 0030_custom_roles
"""
import sqlalchemy as sa
from alembic import op

revision = "0031_host_monitoring_mode"
down_revision = "0030_custom_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "hosts",
        sa.Column("monitoring_mode", sa.String(16), nullable=False, server_default="agentless"),
    )
    op.add_column("hosts", sa.Column("ssh_config", sa.JSON(), nullable=True))
    op.create_index("ix_hosts_monitoring_mode", "hosts", ["monitoring_mode"])


def downgrade() -> None:
    op.drop_index("ix_hosts_monitoring_mode", table_name="hosts")
    op.drop_column("hosts", "ssh_config")
    op.drop_column("hosts", "monitoring_mode")
