"""006 — Evidence Chain, Negotiation Sessions, MCP Tool Log

Revision ID: 006_evidence_negotiation_mcp
Revises: 005_orders_payments
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "006_evidence_negotiation_mcp"
down_revision: Union[str, None] = "005_orders_payments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Evidence Chains ──────────────────────────────
    op.create_table(
        "evidence_chains",
        sa.Column("chain_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("head_hash", sa.String(64), nullable=False),
        sa.Column("length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("entity_type", "entity_id", name="ux_evidence_chain_entity"),
    )

    op.create_table(
        "evidence_records",
        sa.Column("record_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("chain_id", UUID(as_uuid=True),
                  sa.ForeignKey("evidence_chains.chain_id"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("data", JSONB(), nullable=False),
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("record_hash", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("chain_id", "sequence", name="ux_evidence_chain_seq"),
        sa.CheckConstraint("sequence >= 0", name="ck_evidence_seq_non_neg"),
    )
    op.create_index("ix_evidence_records_chain", "evidence_records", ["chain_id", "sequence"])

    # ── Negotiation Sessions ─────────────────────────
    op.create_table(
        "negotiation_sessions",
        sa.Column("negotiation_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.agent_id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("constraints", JSONB(), nullable=True),
        sa.Column("best_offer_id", UUID(as_uuid=True), nullable=True),
        sa.Column("rounds_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('open', 'awaiting_offers', 'evaluating', 'counter_proposed', "
            "'accepted', 'rejected', 'timeout', 'cancelled')",
            name="ck_negotiation_status_valid",
        ),
        sa.CheckConstraint("rounds_completed >= 0 AND rounds_completed <= 5",
                          name="ck_negotiation_rounds_bounded"),
    )
    op.create_index("ix_negotiation_user", "negotiation_sessions", ["user_id"])

    op.create_table(
        "negotiation_offers",
        sa.Column("offer_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("negotiation_id", UUID(as_uuid=True),
                  sa.ForeignKey("negotiation_sessions.negotiation_id"), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchants.merchant_id"), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False),
        sa.Column("sku", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("unit_price_paise", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("discount_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("shipping_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tax_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_paise", sa.BigInteger(), nullable=False),
        sa.Column("warranty_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shipping_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("returnable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("return_window_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("is_counter", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_pruned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("proposed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("unit_price_paise > 0", name="ck_offer_price_positive"),
        sa.CheckConstraint("quantity > 0", name="ck_offer_qty_positive"),
        sa.CheckConstraint("round_number >= 1 AND round_number <= 5",
                          name="ck_offer_round_bounded"),
    )
    op.create_index("ix_offers_negotiation", "negotiation_offers", ["negotiation_id", "round_number"])

    # ── MCP Tool Invocation Log ──────────────────────
    op.create_table(
        "mcp_tool_log",
        sa.Column("invocation_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.agent_id"), nullable=False),
        sa.Column("tool_name", sa.String(50), nullable=False),
        sa.Column("parameters", JSONB(), nullable=False),
        sa.Column("capability_check_passed", sa.Boolean(), nullable=False),
        sa.Column("result_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_mcp_log_agent", "mcp_tool_log", ["agent_id", "created_at"])
    op.create_index("ix_mcp_log_tool", "mcp_tool_log", ["tool_name", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_mcp_log_tool", table_name="mcp_tool_log")
    op.drop_index("ix_mcp_log_agent", table_name="mcp_tool_log")
    op.drop_table("mcp_tool_log")
    op.drop_index("ix_offers_negotiation", table_name="negotiation_offers")
    op.drop_table("negotiation_offers")
    op.drop_index("ix_negotiation_user", table_name="negotiation_sessions")
    op.drop_table("negotiation_sessions")
    op.drop_index("ix_evidence_records_chain", table_name="evidence_records")
    op.drop_table("evidence_records")
    op.drop_table("evidence_chains")
