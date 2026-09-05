"""
Transactra — Negotiation Solver Tests

Validates:
- Dominance pruning (Pareto correctness)
- Constraint filtering
- Deterministic ranking
- Session round management
- Bounds enforcement

All O(1) per test — no DB, no network.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from backend.kernel.negotiation.solver import (
    MAX_ROUNDS,
    NegotiationConstraints,
    NegotiationOffer,
    NegotiationSession,
    NegotiationStatus,
    filter_by_constraints,
    offer_dominates,
    prune_dominated,
    rank_offers,
)


# ── Helper ───────────────────────────────────────────

def _offer(
    total_paise: int = 6_800_000,
    shipping_days: int = 3,
    warranty_months: int = 12,
    return_window_days: int = 7,
    merchant_id=None,
    **kwargs,
) -> NegotiationOffer:
    return NegotiationOffer(
        offer_id=uuid4(),
        negotiation_id=uuid4(),
        round_number=1,
        merchant_id=merchant_id or uuid4(),
        product_id=uuid4(),
        sku="TST-001",
        title="Test Product",
        unit_price_paise=total_paise,
        quantity=1,
        shipping_days=shipping_days,
        warranty_months=warranty_months,
        return_window_days=return_window_days,
        **kwargs,
    )


# ═══════════════════════════════════════════════════════
# Dominance
# ═══════════════════════════════════════════════════════

class TestDominance:

    def test_strictly_better_dominates(self) -> None:
        a = _offer(total_paise=5_000_000, shipping_days=2, warranty_months=24)
        b = _offer(total_paise=7_000_000, shipping_days=5, warranty_months=12)
        assert offer_dominates(a, b)
        assert not offer_dominates(b, a)

    def test_equal_does_not_dominate(self) -> None:
        a = _offer(total_paise=5_000_000, shipping_days=3, warranty_months=12)
        b = _offer(total_paise=5_000_000, shipping_days=3, warranty_months=12)
        assert not offer_dominates(a, b)
        assert not offer_dominates(b, a)

    def test_tradeoff_no_dominance(self) -> None:
        """Cheaper but slower vs expensive but faster → no dominance."""
        a = _offer(total_paise=5_000_000, shipping_days=10, warranty_months=12)
        b = _offer(total_paise=7_000_000, shipping_days=2, warranty_months=12)
        assert not offer_dominates(a, b)
        assert not offer_dominates(b, a)

    def test_one_criterion_better_rest_equal(self) -> None:
        a = _offer(total_paise=5_000_000, shipping_days=3, warranty_months=12)
        b = _offer(total_paise=5_000_000, shipping_days=3, warranty_months=6)
        assert offer_dominates(a, b)  # a has better warranty
        assert not offer_dominates(b, a)


# ═══════════════════════════════════════════════════════
# Pruning
# ═══════════════════════════════════════════════════════

class TestPruning:

    def test_empty_list(self) -> None:
        surviving, pruned = prune_dominated([])
        assert surviving == []
        assert pruned == []

    def test_single_offer(self) -> None:
        o = _offer()
        surviving, pruned = prune_dominated([o])
        assert len(surviving) == 1
        assert len(pruned) == 0

    def test_dominated_removed(self) -> None:
        good = _offer(total_paise=5_000_000, shipping_days=2, warranty_months=24)
        bad = _offer(total_paise=8_000_000, shipping_days=5, warranty_months=6)
        surviving, pruned = prune_dominated([good, bad])
        assert len(surviving) == 1
        assert surviving[0] is good
        assert len(pruned) == 1
        assert pruned[0] is bad

    def test_pareto_front_preserved(self) -> None:
        """Non-dominated offers form the Pareto front."""
        cheap_slow = _offer(total_paise=3_000_000, shipping_days=10, warranty_months=6)
        mid = _offer(total_paise=5_000_000, shipping_days=5, warranty_months=12)
        expensive_fast = _offer(total_paise=8_000_000, shipping_days=1, warranty_months=24)
        surviving, pruned = prune_dominated([cheap_slow, mid, expensive_fast])
        # All are on the Pareto front (tradeoffs)
        assert len(surviving) == 3
        assert len(pruned) == 0

    def test_multiple_dominated(self) -> None:
        best = _offer(total_paise=3_000_000, shipping_days=1, warranty_months=36)
        med = _offer(total_paise=5_000_000, shipping_days=3, warranty_months=12)
        worst = _offer(total_paise=8_000_000, shipping_days=7, warranty_months=6)
        surviving, pruned = prune_dominated([best, med, worst])
        assert len(surviving) == 1
        assert surviving[0] is best
        assert len(pruned) == 2


# ═══════════════════════════════════════════════════════
# Constraint Filtering
# ═══════════════════════════════════════════════════════

class TestConstraintFiltering:

    def test_max_total_filter(self) -> None:
        constraints = NegotiationConstraints(max_total_paise=6_000_000)
        offers = [
            _offer(total_paise=5_000_000),
            _offer(total_paise=7_000_000),
            _offer(total_paise=6_000_000),
        ]
        passing, rejected = filter_by_constraints(offers, constraints)
        assert len(passing) == 2
        assert len(rejected) == 1

    def test_warranty_filter(self) -> None:
        constraints = NegotiationConstraints(
            max_total_paise=99_999_999, min_warranty_months=12
        )
        offers = [
            _offer(warranty_months=6),
            _offer(warranty_months=12),
            _offer(warranty_months=24),
        ]
        passing, rejected = filter_by_constraints(offers, constraints)
        assert len(passing) == 2

    def test_shipping_filter(self) -> None:
        constraints = NegotiationConstraints(
            max_total_paise=99_999_999, max_shipping_days=5
        )
        offers = [
            _offer(shipping_days=3),
            _offer(shipping_days=7),
            _offer(shipping_days=5),
        ]
        passing, rejected = filter_by_constraints(offers, constraints)
        assert len(passing) == 2

    def test_returnable_filter(self) -> None:
        constraints = NegotiationConstraints(
            max_total_paise=99_999_999, require_returnable=True
        )
        offers = [
            _offer(returnable=True),
            _offer(returnable=False),
        ]
        passing, rejected = filter_by_constraints(offers, constraints)
        assert len(passing) == 1

    def test_zero_max_total_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            NegotiationConstraints(max_total_paise=0)


# ═══════════════════════════════════════════════════════
# Ranking
# ═══════════════════════════════════════════════════════

class TestRanking:

    def test_cheapest_first(self) -> None:
        offers = [
            _offer(total_paise=8_000_000),
            _offer(total_paise=3_000_000),
            _offer(total_paise=5_000_000),
        ]
        ranked = rank_offers(offers)
        assert ranked[0].total_paise == 3_000_000
        assert ranked[1].total_paise == 5_000_000
        assert ranked[2].total_paise == 8_000_000

    def test_tiebreak_by_shipping(self) -> None:
        offers = [
            _offer(total_paise=5_000_000, shipping_days=7),
            _offer(total_paise=5_000_000, shipping_days=2),
        ]
        ranked = rank_offers(offers)
        assert ranked[0].shipping_days == 2

    def test_tiebreak_by_warranty(self) -> None:
        offers = [
            _offer(total_paise=5_000_000, shipping_days=3, warranty_months=6),
            _offer(total_paise=5_000_000, shipping_days=3, warranty_months=24),
        ]
        ranked = rank_offers(offers)
        assert ranked[0].warranty_months == 24  # more warranty is better


# ═══════════════════════════════════════════════════════
# Session
# ═══════════════════════════════════════════════════════

class TestNegotiationSession:

    def test_single_round(self) -> None:
        session = NegotiationSession(
            constraints=NegotiationConstraints(max_total_paise=10_000_000)
        )
        offers = [
            _offer(total_paise=5_000_000, shipping_days=3, warranty_months=12),
            _offer(total_paise=8_000_000, shipping_days=5, warranty_months=6),
            _offer(total_paise=12_000_000, shipping_days=1, warranty_months=24),
        ]
        result = session.evaluate_round(offers)
        assert result.round_number == 1
        assert len(result.constraint_filtered) == 1  # 12M exceeds constraint
        assert len(result.ranked) >= 1
        assert session.best_offer is not None
        assert session.best_offer.total_paise <= 10_000_000

    def test_multi_round(self) -> None:
        session = NegotiationSession(
            constraints=NegotiationConstraints(max_total_paise=10_000_000)
        )
        # Round 1
        r1 = session.evaluate_round([
            _offer(total_paise=8_000_000),
            _offer(total_paise=9_000_000),
        ])
        assert r1.round_number == 1

        # Round 2 — better offers
        r2 = session.evaluate_round([
            _offer(total_paise=6_000_000),
            _offer(total_paise=7_000_000),
        ])
        assert r2.round_number == 2
        assert session.best_offer.total_paise == 6_000_000

    def test_max_rounds_enforced(self) -> None:
        session = NegotiationSession()
        for i in range(MAX_ROUNDS):
            session.evaluate_round([_offer()])

        with pytest.raises(ValueError, match="Maximum rounds"):
            session.evaluate_round([_offer()])

    def test_accept_best(self) -> None:
        session = NegotiationSession()
        session.evaluate_round([_offer(total_paise=5_000_000)])
        accepted = session.accept_best()
        assert accepted is not None
        assert accepted.total_paise == 5_000_000
        assert session.status == NegotiationStatus.ACCEPTED

    def test_accept_none_when_empty(self) -> None:
        session = NegotiationSession()
        assert session.accept_best() is None

    def test_cancel(self) -> None:
        session = NegotiationSession()
        session.cancel()
        assert session.status == NegotiationStatus.CANCELLED

    def test_timeout(self) -> None:
        session = NegotiationSession()
        session.timeout()
        assert session.status == NegotiationStatus.TIMEOUT


# ═══════════════════════════════════════════════════════
# Offer Validation
# ═══════════════════════════════════════════════════════

class TestOfferValidation:

    def test_zero_price_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            NegotiationOffer(
                offer_id=uuid4(), negotiation_id=uuid4(), round_number=1,
                merchant_id=uuid4(), product_id=uuid4(), sku="TST",
                title="Test", unit_price_paise=0, quantity=1,
            )

    def test_auto_total(self) -> None:
        o = _offer(total_paise=6_800_000)
        assert o.total_paise == 6_800_000

    def test_frozen(self) -> None:
        o = _offer()
        with pytest.raises(AttributeError):
            o.total_paise = 0  # type: ignore[misc]
