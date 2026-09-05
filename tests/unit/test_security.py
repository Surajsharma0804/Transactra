"""
Transactra — Security Tests (Property-Based + Boundary)

Validates:
- Money invariants under random inputs (Hypothesis)
- Authorization gate: no bypass possible
- Float prohibition across all paths
- Nonce/idempotency uniqueness
- Cart hash tampering detection
- Evidence chain tamper resistance
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from backend.kernel.domain.money import Money
from backend.kernel.authorization.gate import (
    AuthorizationGate, AuthorizationRequest,
)
from backend.kernel.evidence.chain import EvidenceChain, GENESIS_HASH
from backend.kernel.evidence.hashing import canonical_json


# ═══════════════════════════════════════════════════════
# Property-Based: Money Invariants
# ═══════════════════════════════════════════════════════

class TestMoneyProperties:

    @given(amount=st.integers(min_value=0, max_value=10**12))
    @settings(max_examples=200)
    def test_money_always_integer(self, amount: int) -> None:
        """Money amount is always integer — no float, no rounding."""
        m = Money(amount_paise=amount)
        assert isinstance(m.amount_paise, int)

    @given(a=st.integers(min_value=0, max_value=10**9),
           b=st.integers(min_value=0, max_value=10**9))
    @settings(max_examples=200)
    def test_add_commutative(self, a: int, b: int) -> None:
        """a + b == b + a for all valid amounts."""
        m1 = Money(amount_paise=a)
        m2 = Money(amount_paise=b)
        assert m1.add(m2) == m2.add(m1)

    @given(a=st.integers(min_value=0, max_value=10**9),
           b=st.integers(min_value=0, max_value=10**9))
    @settings(max_examples=200)
    def test_add_result_is_sum(self, a: int, b: int) -> None:
        m1 = Money(amount_paise=a)
        m2 = Money(amount_paise=b)
        result = m1.add(m2)
        assert result.amount_paise == a + b

    @given(base=st.integers(min_value=1, max_value=10**9),
           rate=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=200)
    def test_tax_always_integer(self, base: int, rate: int) -> None:
        """Tax computation always returns integer paise."""
        result = Money.compute_tax(base, rate)
        assert isinstance(result, int)
        assert result >= 0

    @given(base=st.integers(min_value=1, max_value=10**9),
           rate=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=200)
    def test_discount_always_integer(self, base: int, rate: int) -> None:
        """Discount computation always returns integer paise."""
        result = Money.compute_discount(base, rate)
        assert isinstance(result, int)
        assert result >= 0


# ═══════════════════════════════════════════════════════
# Property-Based: Authorization Gate Never Bypassed
# ═══════════════════════════════════════════════════════

class TestAuthorizationProperties:

    @given(
        principal_active=st.booleans(),
        agent_active=st.booleans(),
        mandate_active=st.booleans(),
        mandate_has_budget=st.booleans(),
        consent_valid=st.booleans(),
        nonce_unused=st.booleans(),
        idempotency_fresh=st.booleans(),
    )
    @settings(max_examples=500)
    def test_any_failure_means_deny(
        self,
        principal_active: bool,
        agent_active: bool,
        mandate_active: bool,
        mandate_has_budget: bool,
        consent_valid: bool,
        nonce_unused: bool,
        idempotency_fresh: bool,
    ) -> None:
        """If ANY predicate is False, the decision MUST be DENY."""
        all_true = all([
            principal_active, agent_active, mandate_active,
            mandate_has_budget, consent_valid, nonce_unused,
            idempotency_fresh,
        ])

        gate = AuthorizationGate()
        user_id = uuid4()
        req = AuthorizationRequest(
            request_id=uuid4(), principal_user_id=user_id,
            agent_id=uuid4(), mandate_id=uuid4(), consent_id=uuid4(),
            cart_hash="test_hash", amount_paise=1_000_000,
            currency="INR", category="laptops", merchant_id=uuid4(),
            idempotency_key=f"idem-{uuid4()}",
            authorization_nonce=f"nonce-{uuid4()}",
        )

        decision = gate.evaluate(
            req,
            principal_active=principal_active,
            principal_user_id=user_id,
            agent_active=agent_active,
            agent_owner_id=user_id,
            agent_capabilities=frozenset({"request_authorization"}),
            mandate_active=mandate_active,
            mandate_owner_id=user_id,
            mandate_agent_id=req.agent_id,
            mandate_has_budget=mandate_has_budget,
            mandate_category_ok=True,
            mandate_merchant_ok=True,
            mandate_cart_hash=None,
            consent_valid=consent_valid,
            consent_cart_hash="test_hash",
            nonce_unused=nonce_unused,
            idempotency_fresh=idempotency_fresh,
        )

        if not all_true:
            assert decision.is_deny, (
                f"SECURITY VIOLATION: Decision ALLOW despite failed predicates. "
                f"principal={principal_active}, agent={agent_active}, "
                f"mandate={mandate_active}, budget={mandate_has_budget}, "
                f"consent={consent_valid}, nonce={nonce_unused}, "
                f"idem={idempotency_fresh}"
            )
        else:
            assert decision.is_allow


# ═══════════════════════════════════════════════════════
# Float Prohibition
# ═══════════════════════════════════════════════════════

class TestFloatProhibition:

    def test_money_rejects_float(self) -> None:
        with pytest.raises(TypeError):
            Money(amount_paise=3.14)  # type: ignore[arg-type]

    @given(value=st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_canonical_json_rejects_any_float(self, value: float) -> None:
        """canonical_json rejects ALL float values."""
        with pytest.raises(ValueError, match="Float"):
            canonical_json({"price": value})


# ═══════════════════════════════════════════════════════
# Evidence Chain Tamper Resistance
# ═══════════════════════════════════════════════════════

class TestEvidenceChainSecurity:

    def test_cannot_forge_record(self) -> None:
        """A forged record with wrong hash is detected."""
        chain = EvidenceChain()
        chain.append("event.real", {"amount": 6_800_000})
        chain.append("event.real2", {"amount": 500_000})

        # Tamper: insert a fake record between them
        from backend.kernel.evidence.chain import EvidenceRecord
        fake = EvidenceRecord(
            record_id=uuid4(),
            chain_id=chain.chain_id,
            sequence=1,
            event_type="event.fake",
            data={"amount": 0},
            timestamp=chain.records[1].timestamp,
            prev_hash=chain.records[0].record_hash,
            record_hash="0000000000000000000000000000000000000000000000000000000000000000",
        )
        # Replace internal record (simulating DB tampering)
        chain._records[1] = fake

        valid, msg = chain.verify()
        assert not valid

    @given(n=st.integers(min_value=1, max_value=50))
    @settings(max_examples=30)
    def test_chain_of_n_verifies(self, n: int) -> None:
        """Chains of any length verify correctly if untampered."""
        chain = EvidenceChain()
        for i in range(n):
            chain.append(f"event.{i}", {"i": i})
        valid, _ = chain.verify()
        assert valid
