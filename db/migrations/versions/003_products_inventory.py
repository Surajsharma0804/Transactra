"""003 — Products, Inventory, Embeddings

Revision ID: 003_products_inventory
Revises: 002_agents_capabilities

Index strategy for optimal search complexity:
- B-tree composite (is_active, category, price_paise): O(log n + k) for structured search
- GIN on JSONB attributes: O(log n) for attribute filtering
- HNSW on vector embeddings: O(log n) approximate nearest neighbor
- Unique (merchant_id, sku): O(log n) SKU lookup
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "003_products_inventory"
down_revision: Union[str, None] = "002_agents_capabilities"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Products ─────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("product_id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("merchant_id", UUID(as_uuid=True), sa.ForeignKey("merchants.merchant_id"), nullable=False),
        sa.Column("sku", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("price_paise", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("attributes", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("warranty_months", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("refurbished", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("shipping_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("shipping_paise", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("returnable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("return_window_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        # CHECK constraints
        sa.CheckConstraint("price_paise > 0", name="ck_products_price_positive"),
        sa.CheckConstraint("warranty_months >= 0", name="ck_products_warranty_non_neg"),
        sa.CheckConstraint("shipping_days >= 0", name="ck_products_ship_days_non_neg"),
        sa.CheckConstraint("shipping_paise >= 0", name="ck_products_ship_paise_non_neg"),
        sa.CheckConstraint("return_window_days >= 0", name="ck_products_return_non_neg"),
        sa.CheckConstraint("length(currency) = 3", name="ck_products_currency_iso"),
        sa.UniqueConstraint("merchant_id", "sku", name="ux_product_merchant_sku"),
    )

    # ── Search indexes (Section 7 of spec) ───────────
    # Primary composite: O(log n + k) for WHERE is_active AND category AND price range
    op.execute(
        "CREATE INDEX ix_products_search ON products(is_active, category, price_paise) "
        "INCLUDE (merchant_id, warranty_months, refurbished) "
        "WHERE is_active"
    )
    op.create_index("ix_products_category", "products", ["category"],
                     postgresql_where=sa.text("is_active"))
    op.create_index("ix_products_price", "products", ["price_paise"],
                     postgresql_where=sa.text("is_active"))
    op.create_index("ix_products_merchant", "products", ["merchant_id"],
                     postgresql_where=sa.text("is_active"))

    # GIN index for JSONB attribute filtering: O(log n) containment queries
    op.execute("CREATE INDEX ix_products_attributes ON products USING GIN (attributes)")

    # ── Inventory ────────────────────────────────────
    op.create_table(
        "inventory",
        sa.Column("product_id", UUID(as_uuid=True),
                  sa.ForeignKey("products.product_id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reserved", sa.Integer(), nullable=False, server_default="0"),
        # Generated column: available = quantity - reserved
        sa.Column("available", sa.Integer(),
                  sa.Computed("quantity - reserved", persisted=True)),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint("quantity >= 0", name="ck_inventory_qty_non_neg"),
        sa.CheckConstraint("reserved >= 0", name="ck_inventory_res_non_neg"),
        sa.CheckConstraint("quantity >= reserved", name="ck_inventory_available_non_neg"),
    )

    # ── Product Embeddings (pgvector) ────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "product_embeddings",
        sa.Column("product_id", UUID(as_uuid=True),
                  sa.ForeignKey("products.product_id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("embedding", sa.Text(), nullable=True),  # vector(1536) — raw SQL below
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    # Alter column to vector type and create HNSW index
    op.execute("ALTER TABLE product_embeddings ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")
    # HNSW index for approximate nearest neighbor: O(log n) search
    op.execute(
        "CREATE INDEX ix_embeddings_vector ON product_embeddings "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 200)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_embeddings_vector")
    op.drop_table("product_embeddings")
    op.drop_table("inventory")
    op.execute("DROP INDEX IF EXISTS ix_products_attributes")
    op.execute("DROP INDEX IF EXISTS ix_products_search")
    op.drop_index("ix_products_merchant", table_name="products")
    op.drop_index("ix_products_price", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_table("products")
