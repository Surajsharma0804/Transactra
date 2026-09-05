"""
Transactra — User and Merchant ORM Models

Migration 001: users + merchants tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    Principal / consent giver.
    Trust level: Highest for intent/consent.
    """

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    identity_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="active",
    )

    # Relationships
    merchants: Mapped[list[Merchant]] = relationship(back_populates="owner")
    agents: Mapped[list["Agent"]] = relationship(back_populates="owner")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended', 'deleted')",
            name="status_valid",
        ),
    )


class Merchant(Base, TimestampMixin):
    """
    Merchant account. Owns products, policies, and merchant agents.
    """

    __tablename__ = "merchants"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    merchant_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="active",
    )

    # Relationships
    owner: Mapped[User] = relationship(back_populates="merchants", foreign_keys=[owner_user_id])

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended', 'deleted')",
            name="status_valid",
        ),
        Index("ix_merchants_owner", "owner_user_id"),
        # FK defined via relationship
        {"comment": "Merchant accounts with ownership tracking"},
    )
