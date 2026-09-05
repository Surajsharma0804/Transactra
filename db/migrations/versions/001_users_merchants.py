"""001 — Users and Merchants

Revision ID: 001_users_merchants
Revises: None
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001_users_merchants"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Users ────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("user_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("identity_key", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="ck_users_status_valid"),
        sa.UniqueConstraint("email", name="ux_users_email"),
        sa.UniqueConstraint("identity_key", name="ux_users_identity_key"),
    )

    # ── Merchants ────────────────────────────────────
    op.create_table(
        "merchants",
        sa.Column("merchant_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("merchant_key", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("owner_user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="ck_merchants_status_valid"),
        sa.UniqueConstraint("merchant_key", name="ux_merchants_key"),
    )
    op.create_index("ix_merchants_owner", "merchants", ["owner_user_id"])


def downgrade() -> None:
    op.drop_index("ix_merchants_owner", table_name="merchants")
    op.drop_table("merchants")
    op.drop_table("users")
