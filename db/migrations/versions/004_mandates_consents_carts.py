"""004 — Mandates, Consents, Carts

Revision ID: 004_mandates_consents_carts
Revises: 003_products_inventory

Core authorization tables with separated idempotency and nonce,
CHECK constraints for type-specific field control, and cart total validation.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "004_mandates_consents_carts"
down_revision: Union[str, None] = "003_products_inventory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Mandates ─────────────────────────────────────
    op.create_table(
        "mandates",
        sa.Column("mandate_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.agent_id"), nullable=False),
        sa.Column("mandate_type", sa.String(20), nullable=False),
        sa.Column("max_amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("used_amount_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("allowed_categories", sa.ARRAY(sa.Text()), nullable=True),
        sa.Column("allowed_merchant_ids", sa.ARRAY(UUID(as_uuid=True)), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        # Cart binding (set on authorization, not creation)
        sa.Column("cart_hash", sa.String(64), nullable=True),
        sa.Column("bound_amount_paise", sa.BigInteger(), nullable=True),
        # Time window
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # CHECK constraints
        sa.CheckConstraint(
            "mandate_type IN ('per_transaction', 'daily', 'weekly', 'monthly', 'one_time')",
            name="ck_mandates_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'exhausted', 'expired', 'revoked')",
            name="ck_mandates_status_valid",
        ),
        sa.CheckConstraint("max_amount_paise > 0", name="ck_mandates_max_positive"),
        sa.CheckConstraint("used_amount_paise >= 0", name="ck_mandates_used_non_neg"),
        sa.CheckConstraint("used_amount_paise <= max_amount_paise", name="ck_mandates_used_within_max"),
        sa.CheckConstraint("length(currency) = 3", name="ck_mandates_currency_iso"),
        # Type-specific field control: ONE_TIME mandates require cart binding when bound
        sa.CheckConstraint(
            "(mandate_type != 'one_time') OR "
            "(cart_hash IS NULL AND bound_amount_paise IS NULL) OR "
            "(cart_hash IS NOT NULL AND bound_amount_paise IS NOT NULL)",
            name="ck_mandates_one_time_binding",
        ),
        # Bound amount must not exceed max
        sa.CheckConstraint(
            "bound_amount_paise IS NULL OR bound_amount_paise <= max_amount_paise",
            name="ck_mandates_bound_within_max",
        ),
    )
    op.create_index("ix_mandates_user_active", "mandates", ["user_id", "status"],
                     postgresql_where=sa.text("status = 'active'"))
    op.create_index("ix_mandates_agent", "mandates", ["agent_id"])

    # ── Consents ─────────────────────────────────────
    op.create_table(
        "consents",
        sa.Column("consent_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("mandate_id", UUID(as_uuid=True), sa.ForeignKey("mandates.mandate_id"), nullable=False),
        sa.Column("cart_hash", sa.String(64), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        # CHECK constraints
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired', 'consumed')",
            name="ck_consents_status_valid",
        ),
        sa.CheckConstraint("amount_paise > 0", name="ck_consents_amount_positive"),
        # consumed_at must be set when status is consumed
        sa.CheckConstraint(
            "(status != 'consumed') OR consumed_at IS NOT NULL",
            name="ck_consents_consumed_has_timestamp",
        ),
    )
    op.create_index("ix_consents_user", "consents", ["user_id"])
    op.create_index("ix_consents_mandate", "consents", ["mandate_id"])
    op.create_index("ix_consents_active", "consents", ["user_id", "status"],
                     postgresql_where=sa.text("status = 'approved'"))

    # ── Carts ────────────────────────────────────────
    op.create_table(
        "carts",
        sa.Column("cart_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.agent_id"), nullable=False),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchants.merchant_id"), nullable=False),
        sa.Column("subtotal_paise", sa.BigInteger(), nullable=False),
        sa.Column("shipping_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("tax_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("discount_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("cart_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("warranty_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # CHECK constraints
        sa.CheckConstraint(
            "status IN ('open', 'priced', 'consent_pending', 'authorized', "
            "'payment_pending', 'paid', 'expired', 'cancelled')",
            name="ck_carts_status_valid",
        ),
        sa.CheckConstraint("subtotal_paise >= 0", name="ck_carts_subtotal_non_neg"),
        sa.CheckConstraint("shipping_paise >= 0", name="ck_carts_shipping_non_neg"),
        sa.CheckConstraint("tax_paise >= 0", name="ck_carts_tax_non_neg"),
        sa.CheckConstraint("discount_paise >= 0", name="ck_carts_discount_non_neg"),
        sa.CheckConstraint("total_paise >= 0", name="ck_carts_total_non_neg"),
        # Cart total = subtotal + shipping + tax - discount
        sa.CheckConstraint(
            "total_paise = subtotal_paise + shipping_paise + tax_paise - discount_paise",
            name="ck_carts_total_formula",
        ),
        # Discount cannot exceed subtotal + shipping + tax
        sa.CheckConstraint(
            "discount_paise <= subtotal_paise + shipping_paise + tax_paise",
            name="ck_carts_discount_within_value",
        ),
    )
    op.create_index("ix_carts_user", "carts", ["user_id"])

    # ── Cart Items ───────────────────────────────────
    op.create_table(
        "cart_items",
        sa.Column("cart_item_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("cart_id", UUID(as_uuid=True), sa.ForeignKey("carts.cart_id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchants.merchant_id"), nullable=False),
        sa.Column("sku", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_paise", sa.BigInteger(), nullable=False),
        sa.Column("discount_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("line_total_paise", sa.BigInteger(), nullable=False),
        # CHECK constraints
        sa.CheckConstraint("quantity > 0", name="ck_cart_items_qty_positive"),
        sa.CheckConstraint("unit_price_paise > 0", name="ck_cart_items_price_positive"),
        sa.CheckConstraint("discount_paise >= 0", name="ck_cart_items_discount_non_neg"),
        sa.CheckConstraint("line_total_paise >= 0", name="ck_cart_items_total_non_neg"),
        # Line total = (unit_price × quantity) - discount
        sa.CheckConstraint(
            "line_total_paise = (unit_price_paise * quantity) - discount_paise",
            name="ck_cart_items_total_formula",
        ),
    )
    op.create_index("ix_cart_items_cart", "cart_items", ["cart_id"])


def downgrade() -> None:
    op.drop_index("ix_cart_items_cart", table_name="cart_items")
    op.drop_table("cart_items")
    op.drop_index("ix_carts_user", table_name="carts")
    op.drop_table("carts")
    op.drop_index("ix_consents_active", table_name="consents")
    op.drop_index("ix_consents_mandate", table_name="consents")
    op.drop_index("ix_consents_user", table_name="consents")
    op.drop_table("consents")
    op.drop_index("ix_mandates_agent", table_name="mandates")
    op.drop_index("ix_mandates_user_active", table_name="mandates")
    op.drop_table("mandates")
