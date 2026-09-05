"""005 — Orders, Payments, Authorization Log

Revision ID: 005_orders_payments
Revises: 004_mandates_consents_carts

Dual-state payment architecture:
- local_state: what we did (initiated → requested → acknowledged)
- provider_confirmed_state: what webhook confirmed (captured/failed)
- Only webhook is authoritative

Separated idempotency_key and authorization_nonce columns.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "005_orders_payments"
down_revision: Union[str, None] = "004_mandates_consents_carts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Authorization Log ────────────────────────────
    op.create_table(
        "authorization_log",
        sa.Column("decision_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("request_id", UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.agent_id"), nullable=False),
        sa.Column("mandate_id", UUID(as_uuid=True), sa.ForeignKey("mandates.mandate_id"), nullable=False),
        sa.Column("consent_id", UUID(as_uuid=True), sa.ForeignKey("consents.consent_id"), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        sa.Column("failed_rule_id", sa.String(50), nullable=True),
        sa.Column("failed_reason", sa.Text(), nullable=True),
        sa.Column("rule_trail", JSONB(), nullable=False),
        sa.Column("snapshot", JSONB(), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("cart_hash", sa.String(64), nullable=False),
        # Separated: idempotency vs nonce
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("authorization_nonce", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # Unique constraints for idempotency and replay protection
        sa.UniqueConstraint("idempotency_key", name="ux_authlog_idempotency"),
        sa.UniqueConstraint("authorization_nonce", name="ux_authlog_nonce"),
    )
    op.create_index("ix_authlog_user", "authorization_log", ["user_id"])

    # ── Orders ───────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("order_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("cart_id", UUID(as_uuid=True), sa.ForeignKey("carts.cart_id"), nullable=False),
        sa.Column("mandate_id", UUID(as_uuid=True), sa.ForeignKey("mandates.mandate_id"), nullable=False),
        sa.Column("consent_id", UUID(as_uuid=True), sa.ForeignKey("consents.consent_id"), nullable=False),
        sa.Column("authorization_decision_id", UUID(as_uuid=True),
                  sa.ForeignKey("authorization_log.decision_id"), nullable=False),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchants.merchant_id"), nullable=False),
        sa.Column("total_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(20), nullable=False, server_default="created"),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("authorization_nonce", sa.Text(), nullable=False),
        sa.Column("cart_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # CHECK constraints
        sa.CheckConstraint(
            "status IN ('created', 'payment_pending', 'payment_failed', 'paid', "
            "'fulfilling', 'shipped', 'delivered', 'cancelled', 'refunded')",
            name="ck_orders_status_valid",
        ),
        sa.CheckConstraint("total_paise > 0", name="ck_orders_total_positive"),
        sa.UniqueConstraint("idempotency_key", name="ux_orders_idempotency"),
    )
    op.create_index("ix_orders_user", "orders", ["user_id"])
    op.create_index("ix_orders_merchant", "orders", ["merchant_id"])

    # ── Payments (Dual State) ────────────────────────
    op.create_table(
        "payments",
        sa.Column("payment_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.order_id"), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        # Dual state
        sa.Column("local_state", sa.String(30), nullable=False, server_default="initiated"),
        sa.Column("provider_confirmed_state", sa.String(30), nullable=True),
        # Provider references
        sa.Column("provider_order_id", sa.Text(), nullable=True),
        sa.Column("provider_payment_id", sa.Text(), nullable=True),
        sa.Column("provider_signature", sa.Text(), nullable=True),
        # Idempotency
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("provider_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # CHECK constraints
        sa.CheckConstraint(
            "local_state IN ('initiated', 'provider_requested', 'provider_acknowledged', "
            "'provider_error', 'completed', 'failed', 'timeout', 'abandoned')",
            name="ck_payments_local_state_valid",
        ),
        sa.CheckConstraint(
            "provider_confirmed_state IS NULL OR "
            "provider_confirmed_state IN ('captured', 'failed', 'refunded', 'disputed')",
            name="ck_payments_provider_state_valid",
        ),
        sa.CheckConstraint("amount_paise > 0", name="ck_payments_amount_positive"),
        # Provider confirmed state requires confirmed_at
        sa.CheckConstraint(
            "(provider_confirmed_state IS NULL) OR (provider_confirmed_at IS NOT NULL)",
            name="ck_payments_confirmed_has_timestamp",
        ),
        # Paid requires provider_order_id
        sa.CheckConstraint(
            "(provider_confirmed_state != 'captured') OR (provider_order_id IS NOT NULL)",
            name="ck_payments_captured_has_provider_id",
        ),
        sa.UniqueConstraint("idempotency_key", name="ux_payments_idempotency"),
    )
    op.create_index("ix_payments_order", "payments", ["order_id"])
    # Partial index for reconciliation: find payments needing reconciliation
    op.execute(
        "CREATE INDEX ix_payments_needs_reconciliation ON payments(local_state, created_at) "
        "WHERE provider_confirmed_state IS NULL AND "
        "local_state IN ('provider_requested', 'provider_acknowledged', 'timeout')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_payments_needs_reconciliation")
    op.drop_index("ix_payments_order", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_orders_merchant", table_name="orders")
    op.drop_index("ix_orders_user", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_authlog_user", table_name="authorization_log")
    op.drop_table("authorization_log")
