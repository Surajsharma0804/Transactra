"""
Transactra — ORM Models: Order, Payment, AuthorizationLog

Dual-state payment: local_state vs provider_confirmed_state.
Optimistic locking via version column.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base


class AuthorizationLogModel(Base):
    __tablename__ = "authorization_log"

    decision_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    user_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    agent_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    mandate_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("mandates.mandate_id"), nullable=False)
    consent_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("consents.consent_id"), nullable=False)
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failed_rule_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    failed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_trail: Mapped[dict] = mapped_column(JSONB, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cart_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    authorization_nonce: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class OrderModel(Base):
    __tablename__ = "orders"

    order_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    cart_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("carts.cart_id"), nullable=False)
    mandate_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("mandates.mandate_id"), nullable=False)
    consent_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("consents.consent_id"), nullable=False)
    authorization_decision_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("authorization_log.decision_id"), nullable=False)
    merchant_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.merchant_id"), nullable=False)
    total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    idempotency_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    authorization_nonce: Mapped[str] = mapped_column(Text, nullable=False)
    cart_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class PaymentModel(Base):
    __tablename__ = "payments"

    payment_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    local_state: Mapped[str] = mapped_column(String(30), nullable=False, default="initiated")
    provider_confirmed_state: Mapped[str | None] = mapped_column(String(30), nullable=True)
    provider_order_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_payment_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    provider_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
