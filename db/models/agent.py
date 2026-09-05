"""
Transactra — Agent and Capability ORM Models

Migration 002: agents + agent_capabilities tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class Agent(Base, TimestampMixin):
    """
    Agent identity. Untrusted for money.
    Agents propose; the Commerce Kernel decides.

    Index strategy:
    - ix_agents_owner: O(log n) lookup by owner
    - ix_agents_active_expiry: O(log n) find active non-expired agents
    """

    __tablename__ = "agents"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
    )
    agent_type: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="active",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="agents")  # type: ignore[name-defined]
    capabilities: Mapped[list[AgentCapability]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "agent_type IN ('buyer', 'merchant', 'delegated', 'external')",
            name="agent_type_valid",
        ),
        CheckConstraint(
            "status IN ('active', 'suspended', 'revoked', 'expired')",
            name="status_valid",
        ),
        Index("ix_agents_owner", "owner_user_id"),
        Index(
            "ix_agents_active_expiry",
            "status",
            "expires_at",
            postgresql_where=text("status = 'active'"),
        ),
    )


class AgentCapability(Base):
    """
    Allowed actions for an agent. O(1) lookup per capability via PK.

    Capabilities are distinct from authority:
    - Capability = what tools/actions the agent can invoke
    - Authority (mandate) = within what bounds

    Having 'search' capability does not imply payment authority.
    Having 'request_authorization' capability means the agent can
    ASK for authorization, not that it will be granted.
    """

    __tablename__ = "agent_capabilities"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.agent_id", ondelete="CASCADE"),
        nullable=False,
    )
    capability: Mapped[str] = mapped_column(String(30), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # Relationship
    agent: Mapped[Agent] = relationship(back_populates="capabilities")

    __table_args__ = (
        PrimaryKeyConstraint("agent_id", "capability"),
        CheckConstraint(
            "capability IN ("
            "'search', 'compare', 'negotiate', "
            "'propose_cart', 'request_authorization', "
            "'view_proof', 'replay', 'manage_catalog', "
            "'manage_policy', 'approve_offer'"
            ")",
            name="capability_valid",
        ),
    )
