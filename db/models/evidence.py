"""
Transactra — ORM Models: Evidence Chain, Negotiation, MCP Log
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


class EvidenceChainModel(Base):
    __tablename__ = "evidence_chains"

    chain_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), nullable=False)
    head_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class EvidenceRecordModel(Base):
    __tablename__ = "evidence_records"

    record_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    chain_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("evidence_chains.chain_id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    record_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class NegotiationSessionModel(Base):
    __tablename__ = "negotiation_sessions"

    negotiation_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    agent_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    constraints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    best_offer_id: Mapped[uuid4 | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    rounds_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class NegotiationOfferModel(Base):
    __tablename__ = "negotiation_offers"

    offer_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    negotiation_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("negotiation_sessions.negotiation_id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    merchant_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("merchants.merchant_id"), nullable=False)
    product_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    sku: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    unit_price_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    shipping_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    tax_paise: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    warranty_months: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shipping_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    returnable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    return_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    is_counter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_pruned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    proposed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class MCPToolLogModel(Base):
    __tablename__ = "mcp_tool_log"

    invocation_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False)
    capability_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    result_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
