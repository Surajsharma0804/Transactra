"""
Transactra — ORM Models: Mandate, Consent, Cart, CartItem

SQLAlchemy 2.0 mapped_column style.
Optimistic locking via version column.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base


class MandateModel(Base):
    __tablename__ = "mandates"

    mandate_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    agent_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    mandate_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    max_amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    used_amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    allowed_categories: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    allowed_merchant_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ConsentModel(Base):
    __tablename__ = "consents"

    consent_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    mandate_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("mandates.mandate_id"), nullable=False)
    cart_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class CartModel(Base):
    __tablename__ = "carts"

    cart_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    agent_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    merchant_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.merchant_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    subtotal_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    shipping_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    tax_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    discount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    cart_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    items: Mapped[list["CartItemModel"]] = relationship(back_populates="cart", lazy="selectin")


class CartItemModel(Base):
    __tablename__ = "cart_items"

    item_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cart_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("carts.cart_id"), nullable=False)
    product_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    merchant_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.merchant_id"), nullable=False)
    sku: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    line_total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)

    cart: Mapped["CartModel"] = relationship(back_populates="items")
