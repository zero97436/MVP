"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "hosts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hostname_or_ip", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("environment", sa.String(64), server_default="production"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_hosts_name", "hosts", ["name"])
    op.create_index("ix_hosts_environment", "hosts", ["environment"])

    op.create_table(
        "checks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("host_id", sa.Integer, sa.ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("interval_seconds", sa.Integer, nullable=False, server_default="60"),
        sa.Column("timeout_seconds", sa.Integer, nullable=False, server_default="10"),
        sa.Column("warning_threshold", sa.Float),
        sa.Column("critical_threshold", sa.Float),
        sa.Column("config_json", sa.JSON),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_status", sa.String(16)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_checks_host_id", "checks", ["host_id"])
    op.create_index("ix_checks_type", "checks", ["type"])
    op.create_index("ix_checks_last_status", "checks", ["last_status"])

    op.create_table(
        "check_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("check_id", sa.Integer, sa.ForeignKey("checks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("value", sa.Float),
        sa.Column("message", sa.Text),
        sa.Column("perfdata", sa.JSON),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_check_results_check_id", "check_results", ["check_id"])
    op.create_index("ix_check_results_status", "check_results", ["status"])
    op.create_index("ix_check_results_checked_at", "check_results", ["checked_at"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("check_id", sa.Integer, sa.ForeignKey("checks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("previous_status", sa.String(16)),
        sa.Column("message", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_check_id", "alerts", ["check_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_is_active", "alerts", ["is_active"])

    op.create_table(
        "notification_channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("config_json", sa.JSON),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("notification_channels")
    op.drop_table("alerts")
    op.drop_table("check_results")
    op.drop_table("checks")
    op.drop_table("hosts")
    op.drop_table("users")
