"""002 — Agents and Capabilities

Revision ID: 002_agents_capabilities
Revises: 001_users_merchants
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002_agents_capabilities"
down_revision: Union[str, None] = "001_users_merchants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Agents ───────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("agent_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("agent_type", sa.String(20), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "agent_type IN ('buyer', 'merchant', 'delegated', 'external')",
            name="ck_agents_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'revoked', 'expired')",
            name="ck_agents_status_valid",
        ),
    )
    op.create_index("ix_agents_owner", "agents", ["owner_user_id"])
    # Partial index: only active agents — O(log n) lookup for active agent checks
    op.execute(
        "CREATE INDEX ix_agents_active_expiry ON agents(status, expires_at) "
        "WHERE status = 'active'"
    )

    # ── Agent Capabilities ───────────────────────────
    op.create_table(
        "agent_capabilities",
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False),
        sa.Column("capability", sa.String(30), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("agent_id", "capability"),
        sa.CheckConstraint(
            "capability IN ("
            "'search', 'compare', 'negotiate', "
            "'propose_cart', 'request_authorization', "
            "'view_proof', 'replay', 'manage_catalog', "
            "'manage_policy', 'approve_offer'"
            ")",
            name="ck_agent_capabilities_valid",
        ),
    )


def downgrade() -> None:
    op.drop_table("agent_capabilities")
    op.execute("DROP INDEX IF EXISTS ix_agents_active_expiry")
    op.drop_index("ix_agents_owner", table_name="agents")
    op.drop_table("agents")
