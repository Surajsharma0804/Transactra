"""
Transactra — Product and Inventory ORM Models

Migration 003: products, inventory, product_embeddings.

Index strategy (all for optimal search complexity):
- B-tree composite on (is_active, category, price_paise): O(log n + k) structured search
- GIN on attributes JSONB: O(log n) attribute filtering
- HNSW on embeddings: O(log n) approximate nearest neighbor
- Partial index on available inventory: O(log n) stock checks
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    """
    Product in the catalog. Owned by a merchant.

    All prices in paise (integer). No float.
    Attributes stored as JSONB for flexible filtering (GIN-indexed).
    """

    __tablename__ = "products"

    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("merchants.merchant_id"),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    category: Mapped[str] = mapped_column(Text, nullable=False)
    price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    refurbished: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    shipping_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="7")
    shipping_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default="0")
    returnable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    return_window_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="7")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    # Relationships
    inventory: Mapped["Inventory | None"] = relationship(back_populates="product", uselist=False)

    __table_args__ = (
        CheckConstraint("price_paise > 0", name="price_positive"),
        CheckConstraint("warranty_months >= 0", name="warranty_non_negative"),
        CheckConstraint("shipping_days >= 0", name="shipping_days_non_negative"),
        CheckConstraint("shipping_paise >= 0", name="shipping_paise_non_negative"),
        CheckConstraint("return_window_days >= 0", name="return_window_non_negative"),
        CheckConstraint("length(currency) = 3", name="currency_iso"),
        # Unique SKU per merchant
        {"comment": "Product catalog with JSONB attributes for flexible filtering"},
    )


class Inventory(Base):
    """
    Inventory for a product. Quantity and reservation tracking.

    available = quantity - reserved (computed column in DB).
    Reservation uses SELECT FOR UPDATE to prevent overselling.

    Complexity:
    - Stock check: O(1) single row read
    - Reservation: O(1) row lock + update
    """

    __tablename__ = "inventory"

    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.product_id", ondelete="CASCADE"),
        primary_key=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # 'available' is a generated column in PostgreSQL — see migration
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationship
    product: Mapped[Product] = relationship(back_populates="inventory")

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("reserved >= 0", name="reserved_non_negative"),
        CheckConstraint("quantity >= reserved", name="available_non_negative"),
    )
