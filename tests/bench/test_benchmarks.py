"""
Transactra — Performance Benchmarks

Uses pytest-benchmark for precise measurement of hot-path operations.
Target budgets from spec:
- Authorization gate: < 100µs
- Cart hash: < 50µs for 10 items
- State machine transition: < 10µs
- Money arithmetic: < 5µs
- Dominance pruning: < 1ms for 100 offers
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from backend.kernel.domain.money import Money
from backend.kernel.domain.state_machine import StateMachine, TransitionRule
from backend.kernel.domain.commerce_states import CART_SM, ORDER_SM
from backend.kernel.authorization.gate import AuthorizationGate, AuthorizationRequest
from backend.kernel.evidence.hashing import canonical_json, canonical_hash, compute_cart_hash
from backend.kernel.evidence.chain import EvidenceChain
from backend.kernel.negotiation.solver import (
    NegotiationOffer, NegotiationConstraints, prune_dominated, rank_offers,
    filter_by_constraints,
)


# ── Helpers ──────────────────────────────────────────

def _make_auth_request():
    user_id = uuid4()
    return AuthorizationRequest(
        request_id=uuid4(), principal_user_id=user_id,
        agent_id=uuid4(), mandate_id=uuid4(), consent_id=uuid4(),
        cart_hash="a" * 64, amount_paise=6_800_000,
        currency="INR", category="laptops", merchant_id=uuid4(),
        idempotency_key=f"idem-{uuid4()}",
        authorization_nonce=f"nonce-{uuid4()}",
    ), user_id


def _all_pass_kwargs(req, user_id):
    return {
        "principal_active": True, "principal_user_id": user_id,
        "agent_active": True, "agent_owner_id": user_id,
        "agent_capabilities": frozenset({"request_authorization"}),
        "mandate_active": True, "mandate_owner_id": user_id,
        "mandate_agent_id": req.agent_id,
        "mandate_has_budget": True, "mandate_category_ok": True,
        "mandate_merchant_ok": True, "mandate_cart_hash": None,
        "consent_valid": True, "consent_cart_hash": req.cart_hash,
        "nonce_unused": True, "idempotency_fresh": True,
    }


# ═══════════════════════════════════════════════════════
# Money Benchmarks
# ═══════════════════════════════════════════════════════

class TestMoneyBenchmarks:

    def test_money_add(self, benchmark) -> None:
        m1 = Money(amount_paise=6_800_000)
        m2 = Money(amount_paise=1_200_000)
        benchmark(m1.add, m2)

    def test_tax_compute(self, benchmark) -> None:
        benchmark(Money.compute_tax, 6_800_000, 1800)

    def test_discount_compute(self, benchmark) -> None:
        benchmark(Money.compute_discount, 6_800_000, 500)

    def test_line_total(self, benchmark) -> None:
        benchmark(Money.compute_line_total, 6_800_000, 3, 200_000)


# ═══════════════════════════════════════════════════════
# State Machine Benchmarks
# ═══════════════════════════════════════════════════════

class TestStateMachineBenchmarks:

    def test_cart_transition(self, benchmark) -> None:
        benchmark(CART_SM.transition, "open", "price")

    def test_order_transition(self, benchmark) -> None:
        benchmark(ORDER_SM.transition, "created", "payment_initiated")


# ═══════════════════════════════════════════════════════
# Authorization Gate Benchmarks
# ═══════════════════════════════════════════════════════

class TestAuthorizationBenchmarks:

    def test_full_allow(self, benchmark) -> None:
        """16-predicate gate full ALLOW path."""
        gate = AuthorizationGate()
        req, user_id = _make_auth_request()
        kwargs = _all_pass_kwargs(req, user_id)
        benchmark(gate.evaluate, req, **kwargs)

    def test_early_deny(self, benchmark) -> None:
        """Short-circuit DENY at predicate 3."""
        gate = AuthorizationGate()
        req, user_id = _make_auth_request()
        kwargs = _all_pass_kwargs(req, user_id)
        kwargs["principal_active"] = False
        benchmark(gate.evaluate, req, **kwargs)


# ═══════════════════════════════════════════════════════
# Hashing Benchmarks
# ═══════════════════════════════════════════════════════

class TestHashingBenchmarks:

    def test_canonical_json_small(self, benchmark) -> None:
        obj = {"amount": 6_800_000, "currency": "INR", "sku": "LAP-001"}
        benchmark(canonical_json, obj)

    def test_cart_hash_10_items(self, benchmark) -> None:
        items = [
            {"product_id": str(uuid4()), "sku": f"SKU-{i:03d}",
             "quantity": i + 1, "unit_price_paise": 1_000_000 * (i + 1),
             "discount_paise": 0, "line_total_paise": 1_000_000 * (i + 1) * (i + 1)}
            for i in range(10)
        ]
        benchmark(compute_cart_hash, uuid4(), items, 55_000_000, 5_000, 990_000, 0, 55_995_000)


# ═══════════════════════════════════════════════════════
# Evidence Chain Benchmarks
# ═══════════════════════════════════════════════════════

class TestEvidenceChainBenchmarks:

    def test_append_record(self, benchmark) -> None:
        chain = EvidenceChain()
        benchmark(chain.append, "test.event", {"key": "value"})

    def test_verify_chain_100(self, benchmark) -> None:
        chain = EvidenceChain()
        for i in range(100):
            chain.append(f"event.{i}", {"i": i})
        benchmark(chain.verify)


# ═══════════════════════════════════════════════════════
# Negotiation Benchmarks
# ═══════════════════════════════════════════════════════

class TestNegotiationBenchmarks:

    def _make_offers(self, n: int) -> list[NegotiationOffer]:
        return [
            NegotiationOffer(
                offer_id=uuid4(), negotiation_id=uuid4(), round_number=1,
                merchant_id=uuid4(), product_id=uuid4(), sku=f"SKU-{i}",
                title=f"Product {i}", unit_price_paise=1_000_000 + i * 100_000,
                quantity=1, shipping_days=2 + (i % 10),
                warranty_months=6 + (i % 36),
            )
            for i in range(n)
        ]

    def test_prune_30_offers(self, benchmark) -> None:
        offers = self._make_offers(30)
        benchmark(prune_dominated, offers)

    def test_prune_100_offers(self, benchmark) -> None:
        offers = self._make_offers(100)
        benchmark(prune_dominated, offers)

    def test_rank_100_offers(self, benchmark) -> None:
        offers = self._make_offers(100)
        benchmark(rank_offers, offers)

    def test_filter_100_offers(self, benchmark) -> None:
        offers = self._make_offers(100)
        constraints = NegotiationConstraints(
            max_total_paise=5_000_000, min_warranty_months=12,
            max_shipping_days=7,
        )
        benchmark(filter_by_constraints, offers, constraints)
