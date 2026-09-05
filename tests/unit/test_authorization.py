"""
Transactra — Authorization Gate Tests

Validates:
- All 16 predicates individually
- Short-circuit evaluation (first failure stops)
- Full ALLOW path
- Fail-closed semantics
- Immutable decision records
- INV-06: cart change after consent → DENY

Every test is O(1) — no DB, no network.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from backend.kernel.authorization.gate import (
    AuthorizationDecision,
    AuthorizationGate,
    AuthorizationRequest,
)


# ── Test Helpers ─────────────────────────────────────

def _make_request(**overrides) -> AuthorizationRequest:
    defaults = {
        "request_id": uuid4(),
        "principal_user_id": uuid4(),
        "agent_id": uuid4(),
        "mandate_id": uuid4(),
        "consent_id": uuid4(),
        "cart_hash": "abc123",
        "amount_paise": 6_800_000,
        "currency": "INR",
        "category": "laptops",
        "merchant_id": uuid4(),
        "idempotency_key": f"idem-{uuid4()}",
        "authorization_nonce": f"nonce-{uuid4()}",
    }
    defaults.update(overrides)
    return AuthorizationRequest(**defaults)


def _all_pass_kwargs(request: AuthorizationRequest) -> dict:
    """Return kwargs that pass all 16 predicates."""
    return {
        "principal_active": True,
        "principal_user_id": request.principal_user_id,
        "agent_active": True,
        "agent_owner_id": request.principal_user_id,
        "agent_capabilities": frozenset({"request_authorization"}),
        "mandate_active": True,
        "mandate_owner_id": request.principal_user_id,
        "mandate_agent_id": request.agent_id,
        "mandate_has_budget": True,
        "mandate_category_ok": True,
        "mandate_merchant_ok": True,
        "mandate_cart_hash": None,
        "consent_valid": True,
        "consent_cart_hash": request.cart_hash,
        "nonce_unused": True,
        "idempotency_fresh": True,
    }


# ═══════════════════════════════════════════════════════
# Full ALLOW path
# ═══════════════════════════════════════════════════════

class TestAuthorizationAllow:

    def test_all_pass_gives_allow(self) -> None:
        gate = AuthorizationGate()
        req = _make_request()
        decision = gate.evaluate(req, **_all_pass_kwargs(req))

        assert decision.is_allow
        assert not decision.is_deny
        assert decision.failed_rule_id is None
        assert len(decision.rule_trail) == 16

    def test_all_rules_passed(self) -> None:
        gate = AuthorizationGate()
        req = _make_request()
        decision = gate.evaluate(req, **_all_pass_kwargs(req))

        for pred in decision.rule_trail:
            assert pred.passed, f"Predicate {pred.rule_id} unexpectedly failed"

    def test_decision_immutable(self) -> None:
        gate = AuthorizationGate()
        req = _make_request()
        decision = gate.evaluate(req, **_all_pass_kwargs(req))

        with pytest.raises(AttributeError):
            decision.allowed = False  # type: ignore[misc]

    def test_snapshot_captured(self) -> None:
        gate = AuthorizationGate()
        req = _make_request()
        decision = gate.evaluate(req, **_all_pass_kwargs(req))

        assert decision.snapshot["amount_paise"] == req.amount_paise
        assert decision.snapshot["cart_hash"] == req.cart_hash
        assert decision.snapshot["category"] == req.category


# ═══════════════════════════════════════════════════════
# Individual predicate failures
# ═══════════════════════════════════════════════════════

class TestAuthorizationDeny:

    def _deny_with_override(self, **overrides) -> AuthorizationDecision:
        gate = AuthorizationGate()
        req = _make_request()
        kwargs = _all_pass_kwargs(req)
        kwargs.update(overrides)
        return gate.evaluate(req, **kwargs)

    def test_principal_inactive_deny(self) -> None:
        decision = self._deny_with_override(principal_active=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_003_PRINCIPAL_ACTIVE"

    def test_agent_inactive_deny(self) -> None:
        decision = self._deny_with_override(agent_active=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_004_AGENT_ACTIVE"

    def test_agent_not_owned_deny(self) -> None:
        decision = self._deny_with_override(agent_owner_id=uuid4())
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_005_AGENT_OWNED"

    def test_mandate_inactive_deny(self) -> None:
        decision = self._deny_with_override(mandate_active=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_007_MANDATE_ACTIVE"

    def test_mandate_not_owned_deny(self) -> None:
        decision = self._deny_with_override(mandate_owner_id=uuid4())
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_008_MANDATE_OWNED"

    def test_category_not_allowed_deny(self) -> None:
        decision = self._deny_with_override(mandate_category_ok=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_009_CATEGORY_ALLOWED"

    def test_budget_insufficient_deny(self) -> None:
        decision = self._deny_with_override(mandate_has_budget=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_010_BUDGET_SUFFICIENT"

    def test_merchant_not_allowed_deny(self) -> None:
        decision = self._deny_with_override(mandate_merchant_ok=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_011_MERCHANT_ALLOWED"

    def test_cart_hash_mismatch_deny(self) -> None:
        decision = self._deny_with_override(mandate_cart_hash="different_hash")
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_012_CART_HASH_MATCHES"

    def test_consent_invalid_deny(self) -> None:
        decision = self._deny_with_override(consent_valid=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_013_CONSENT_VALID"

    def test_consent_cart_mismatch_deny(self) -> None:
        """INV-06: Cart change after consent → DENY."""
        decision = self._deny_with_override(consent_cart_hash="changed_cart_hash")
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_014_CONSENT_CART_MATCHES"

    def test_nonce_reused_deny(self) -> None:
        """Replay attack: reused nonce → DENY."""
        decision = self._deny_with_override(nonce_unused=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_015_NONCE_UNUSED"

    def test_idempotency_duplicate_deny(self) -> None:
        """Duplicate request → DENY."""
        decision = self._deny_with_override(idempotency_fresh=False)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_016_IDEMPOTENCY_FRESH"


# ═══════════════════════════════════════════════════════
# Short-circuit evaluation
# ═══════════════════════════════════════════════════════

class TestShortCircuit:

    def test_first_failure_stops(self) -> None:
        """If predicate 3 fails, predicates 4-16 are not evaluated."""
        gate = AuthorizationGate()
        req = _make_request()
        kwargs = _all_pass_kwargs(req)
        kwargs["principal_active"] = False

        decision = gate.evaluate(req, **kwargs)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_003_PRINCIPAL_ACTIVE"
        # Only predicates 1-3 evaluated (short-circuited at 3)
        assert len(decision.rule_trail) == 3

    def test_later_failure_has_more_trail(self) -> None:
        """If predicate 15 fails, predicates 1-15 are in the trail."""
        gate = AuthorizationGate()
        req = _make_request()
        kwargs = _all_pass_kwargs(req)
        kwargs["nonce_unused"] = False

        decision = gate.evaluate(req, **kwargs)
        assert decision.is_deny
        assert decision.failed_rule_id == "AUTH_015_NONCE_UNUSED"
        assert len(decision.rule_trail) == 15

    def test_multiple_failures_only_first_reported(self) -> None:
        """Even if multiple predicates would fail, only the first matters."""
        gate = AuthorizationGate()
        req = _make_request()
        kwargs = _all_pass_kwargs(req)
        kwargs["principal_active"] = False
        kwargs["agent_active"] = False
        kwargs["mandate_active"] = False

        decision = gate.evaluate(req, **kwargs)
        assert decision.failed_rule_id == "AUTH_003_PRINCIPAL_ACTIVE"
        assert len(decision.rule_trail) == 3


# ═══════════════════════════════════════════════════════
# AuthorizationRequest validation
# ═══════════════════════════════════════════════════════

class TestAuthorizationRequestValidation:

    def test_zero_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            _make_request(amount_paise=0)

    def test_negative_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            _make_request(amount_paise=-100)

    def test_empty_idempotency_key_raises(self) -> None:
        with pytest.raises(ValueError, match="Idempotency"):
            _make_request(idempotency_key="")

    def test_empty_nonce_raises(self) -> None:
        with pytest.raises(ValueError, match="nonce"):
            _make_request(authorization_nonce="")

    def test_empty_cart_hash_raises(self) -> None:
        with pytest.raises(ValueError, match="Cart hash"):
            _make_request(cart_hash="")

    def test_request_immutable(self) -> None:
        req = _make_request()
        with pytest.raises(AttributeError):
            req.amount_paise = 0  # type: ignore[misc]
