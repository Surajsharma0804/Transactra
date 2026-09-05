"""
Transactra — Identity Domain Tests

Validates:
- Agent lifecycle: active/expired/revoked checks
- Capability enforcement: O(1) lookup
- Factory functions: correct defaults
- Immutability of domain types
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.kernel.domain.identity import (
    Agent,
    AgentStatus,
    AgentType,
    Capability,
    Merchant,
    Principal,
    UserStatus,
    create_buyer_agent,
    create_merchant_agent,
)


class TestPrincipal:

    def test_active_principal(self) -> None:
        p = Principal(user_id=uuid4(), email="a@b.com", display_name="A", identity_key="k1")
        assert p.is_active()

    def test_suspended_principal(self) -> None:
        p = Principal(user_id=uuid4(), email="a@b.com", display_name="A",
                      identity_key="k1", status=UserStatus.SUSPENDED)
        assert not p.is_active()

    def test_frozen(self) -> None:
        p = Principal(user_id=uuid4(), email="a@b.com", display_name="A", identity_key="k1")
        with pytest.raises(AttributeError):
            p.email = "x@y.com"  # type: ignore[misc]


class TestAgent:

    def test_active_agent(self) -> None:
        a = Agent(agent_id=uuid4(), owner_user_id=uuid4(),
                  agent_type=AgentType.BUYER, display_name="Bot")
        assert a.is_active()

    def test_expired_agent_denied(self) -> None:
        """INV-04: Expired agents cannot act."""
        a = Agent(
            agent_id=uuid4(), owner_user_id=uuid4(),
            agent_type=AgentType.BUYER, display_name="Bot",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert not a.is_active()

    def test_revoked_agent_denied(self) -> None:
        """INV-04: Revoked agents cannot act."""
        a = Agent(
            agent_id=uuid4(), owner_user_id=uuid4(),
            agent_type=AgentType.BUYER, display_name="Bot",
            status=AgentStatus.REVOKED,
        )
        assert not a.is_active()

    def test_suspended_agent_denied(self) -> None:
        a = Agent(
            agent_id=uuid4(), owner_user_id=uuid4(),
            agent_type=AgentType.BUYER, display_name="Bot",
            status=AgentStatus.SUSPENDED,
        )
        assert not a.is_active()

    def test_future_expiry_is_active(self) -> None:
        a = Agent(
            agent_id=uuid4(), owner_user_id=uuid4(),
            agent_type=AgentType.BUYER, display_name="Bot",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        assert a.is_active()

    def test_no_expiry_is_active(self) -> None:
        a = Agent(
            agent_id=uuid4(), owner_user_id=uuid4(),
            agent_type=AgentType.BUYER, display_name="Bot",
            expires_at=None,
        )
        assert a.is_active()


class TestCapabilities:
    """Capability check is O(1) frozenset lookup."""

    def test_has_capability(self) -> None:
        a = Agent(
            agent_id=uuid4(), owner_user_id=uuid4(),
            agent_type=AgentType.BUYER, display_name="Bot",
            capabilities=frozenset({Capability.SEARCH, Capability.NEGOTIATE}),
        )
        assert a.has_capability(Capability.SEARCH)
        assert a.has_capability(Capability.NEGOTIATE)
        assert not a.has_capability(Capability.REQUEST_AUTHORIZATION)

    def test_has_all_capabilities(self) -> None:
        a = Agent(
            agent_id=uuid4(), owner_user_id=uuid4(),
            agent_type=AgentType.BUYER, display_name="Bot",
            capabilities=frozenset({
                Capability.SEARCH, Capability.NEGOTIATE, Capability.PROPOSE_CART
            }),
        )
        assert a.has_capabilities({Capability.SEARCH, Capability.NEGOTIATE})
        assert not a.has_capabilities({Capability.SEARCH, Capability.MANAGE_CATALOG})

    def test_empty_capabilities(self) -> None:
        a = Agent(
            agent_id=uuid4(), owner_user_id=uuid4(),
            agent_type=AgentType.BUYER, display_name="Bot",
        )
        assert not a.has_capability(Capability.SEARCH)


class TestFactories:

    def test_buyer_agent_capabilities(self) -> None:
        uid = uuid4()
        agent = create_buyer_agent(owner_user_id=uid)
        assert agent.agent_type == AgentType.BUYER
        assert agent.has_capability(Capability.SEARCH)
        assert agent.has_capability(Capability.NEGOTIATE)
        assert agent.has_capability(Capability.PROPOSE_CART)
        assert agent.has_capability(Capability.REQUEST_AUTHORIZATION)
        assert agent.has_capability(Capability.VIEW_PROOF)
        # Buyer cannot manage catalog or policy
        assert not agent.has_capability(Capability.MANAGE_CATALOG)
        assert not agent.has_capability(Capability.MANAGE_POLICY)

    def test_merchant_agent_capabilities(self) -> None:
        uid = uuid4()
        agent = create_merchant_agent(owner_user_id=uid)
        assert agent.agent_type == AgentType.MERCHANT
        assert agent.has_capability(Capability.MANAGE_CATALOG)
        assert agent.has_capability(Capability.MANAGE_POLICY)
        assert agent.has_capability(Capability.APPROVE_OFFER)
        # Merchant cannot request payment authorization
        assert not agent.has_capability(Capability.REQUEST_AUTHORIZATION)


class TestMerchant:

    def test_active_merchant(self) -> None:
        m = Merchant(merchant_id=uuid4(), merchant_key="mk1",
                     display_name="Shop", owner_user_id=uuid4())
        assert m.is_active()

    def test_suspended_merchant(self) -> None:
        m = Merchant(merchant_id=uuid4(), merchant_key="mk1",
                     display_name="Shop", owner_user_id=uuid4(),
                     status=UserStatus.SUSPENDED)
        assert not m.is_active()
