"""
Transactra — Identity Domain Types

Principal (user) and Agent identity types with status lifecycle.
Pure domain types — no framework imports.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


class AgentStatus(str, enum.Enum):
    """Agent lifecycle states. Only ACTIVE agents can act."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AgentType(str, enum.Enum):
    """Type of agent in the system."""
    BUYER = "buyer"
    MERCHANT = "merchant"
    DELEGATED = "delegated"
    EXTERNAL = "external"


class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class Capability(str, enum.Enum):
    """
    Specific actions an agent is allowed to perform.
    Capabilities are distinct from authority — search capability
    does not imply payment authority.
    """
    SEARCH = "search"
    COMPARE = "compare"
    NEGOTIATE = "negotiate"
    PROPOSE_CART = "propose_cart"
    REQUEST_AUTHORIZATION = "request_authorization"
    VIEW_PROOF = "view_proof"
    REPLAY = "replay"
    MANAGE_CATALOG = "manage_catalog"
    MANAGE_POLICY = "manage_policy"
    APPROVE_OFFER = "approve_offer"


@dataclass(frozen=True, slots=True)
class Principal:
    """
    A user/principal in the system. The ultimate source of intent and consent.

    Trust level: Highest for intent/consent.
    Allowed responsibility: Define intent, hard constraints, approval.
    """
    user_id: UUID
    email: str
    display_name: str
    identity_key: str
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        """Check if principal is active. O(1)."""
        return self.status == UserStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class Agent:
    """
    An agent acting on behalf of a principal.

    Trust level: Untrusted for money.
    Agents can search, compare, negotiate, propose — but never
    directly authorize payment or override policy.

    The agent's capabilities define what tools/actions it can invoke.
    The agent's mandate defines the scope of its authority.
    These are independent: capability = "what can you do",
    mandate = "within what bounds".
    """
    agent_id: UUID
    owner_user_id: UUID
    agent_type: AgentType
    display_name: str
    status: AgentStatus = AgentStatus.ACTIVE
    capabilities: frozenset[Capability] = frozenset()
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self, now: datetime | None = None) -> bool:
        """
        Check if agent is active and not expired. O(1).

        An agent is active if:
        1. Status is ACTIVE
        2. Not expired (expires_at is None or in the future)
        """
        if self.status != AgentStatus.ACTIVE:
            return False
        if self.expires_at is not None:
            current = now or datetime.now(timezone.utc)
            if self.expires_at <= current:
                return False
        return True

    def has_capability(self, capability: Capability) -> bool:
        """Check if agent has a specific capability. O(1) set lookup."""
        return capability in self.capabilities

    def has_capabilities(self, required: set[Capability]) -> bool:
        """Check if agent has ALL required capabilities. O(k)."""
        return required.issubset(self.capabilities)


@dataclass(frozen=True, slots=True)
class Merchant:
    """
    A merchant account in the system.

    Merchants have their own policy hierarchy (global → category → product → campaign)
    which constrains what their merchant agents can offer.
    """
    merchant_id: UUID
    merchant_key: str
    display_name: str
    owner_user_id: UUID
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self) -> bool:
        """Check if merchant is active. O(1)."""
        return self.status == UserStatus.ACTIVE


def create_buyer_agent(
    owner_user_id: UUID,
    display_name: str = "Buyer Agent",
    expires_at: datetime | None = None,
) -> Agent:
    """
    Factory for creating a buyer agent with standard capabilities.
    Buyer agents can search, compare, negotiate, propose carts, and
    request authorization — but cannot manage catalog or policy.
    """
    return Agent(
        agent_id=uuid4(),
        owner_user_id=owner_user_id,
        agent_type=AgentType.BUYER,
        display_name=display_name,
        capabilities=frozenset({
            Capability.SEARCH,
            Capability.COMPARE,
            Capability.NEGOTIATE,
            Capability.PROPOSE_CART,
            Capability.REQUEST_AUTHORIZATION,
            Capability.VIEW_PROOF,
        }),
        expires_at=expires_at,
    )


def create_merchant_agent(
    owner_user_id: UUID,
    display_name: str = "Merchant Agent",
    expires_at: datetime | None = None,
) -> Agent:
    """
    Factory for creating a merchant agent with standard capabilities.
    Merchant agents can manage catalog and policy, approve offers,
    but cannot request payment authorization.
    """
    return Agent(
        agent_id=uuid4(),
        owner_user_id=owner_user_id,
        agent_type=AgentType.MERCHANT,
        display_name=display_name,
        capabilities=frozenset({
            Capability.SEARCH,
            Capability.MANAGE_CATALOG,
            Capability.MANAGE_POLICY,
            Capability.APPROVE_OFFER,
            Capability.NEGOTIATE,
        }),
        expires_at=expires_at,
    )
