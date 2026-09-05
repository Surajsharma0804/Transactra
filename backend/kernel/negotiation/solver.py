"""
Transactra — Bounded Negotiation Solver

Multi-round negotiation between buyer and merchant agents.
Uses dominance pruning to eliminate inferior offers early.

Complexity Analysis:
- Offer generation: O(r · m · k) where r=rounds, m=merchants, k=offers/round
- Dominance pruning: O(n²) pairwise comparison per round (n = active offers)
- With pruning: effective n stays small → O(r · m · k · p) where p = surviving offers
- Space: O(n) — only surviving offers kept per round
- Overall bounded: r ≤ MAX_ROUNDS, m ≤ MAX_MERCHANTS, k ≤ MAX_OFFERS_PER_ROUND

Design:
- Negotiation is bounded (max rounds, max time, max offers)
- Each offer is a frozen snapshot — immutable once proposed
- Dominance: offer A dominates offer B if A is ≤ on all criteria and < on at least one
- Pruned offers are logged but not forwarded
- Final selection is deterministic: lowest total, then shortest shipping, then best warranty
"""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import UUID, uuid4


class NegotiationStatus(str, enum.Enum):
    OPEN = "open"
    AWAITING_OFFERS = "awaiting_offers"
    EVALUATING = "evaluating"
    COUNTER_PROPOSED = "counter_proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class NegotiationOffer:
    """
    Single offer in a negotiation round. Immutable snapshot.

    All monetary values in paise (integer). No float.
    """
    offer_id: UUID
    negotiation_id: UUID
    round_number: int
    merchant_id: UUID
    product_id: UUID
    sku: str
    title: str
    unit_price_paise: int
    quantity: int
    discount_paise: int = 0
    shipping_paise: int = 0
    tax_paise: int = 0
    total_paise: int = 0
    warranty_months: int = 0
    shipping_days: int = 7
    returnable: bool = True
    return_window_days: int = 7
    is_counter: bool = False
    proposed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.unit_price_paise <= 0:
            raise ValueError(f"Unit price must be positive: {self.unit_price_paise}")
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive: {self.quantity}")
        expected = (self.unit_price_paise * self.quantity) - self.discount_paise + self.shipping_paise + self.tax_paise
        if self.total_paise == 0:
            object.__setattr__(self, "total_paise", expected)
        elif self.total_paise != expected:
            raise ValueError(
                f"Total mismatch: {self.total_paise} != expected {expected}"
            )


@dataclass(frozen=True, slots=True)
class NegotiationConstraints:
    """
    User-defined constraints for negotiation.
    Agent cannot exceed these bounds.
    """
    max_total_paise: int
    min_warranty_months: int = 0
    max_shipping_days: int = 30
    preferred_categories: frozenset[str] | None = None
    preferred_merchant_ids: frozenset[UUID] | None = None
    require_returnable: bool = False
    min_return_window_days: int = 0

    def __post_init__(self) -> None:
        if self.max_total_paise <= 0:
            raise ValueError(f"Max total must be positive: {self.max_total_paise}")


# ═══════════════════════════════════════════════════════
# Dominance Pruning
# ═══════════════════════════════════════════════════════

def offer_dominates(a: NegotiationOffer, b: NegotiationOffer) -> bool:
    """
    Check if offer A dominates offer B (Pareto dominance).

    A dominates B if A is ≤ on ALL criteria and strictly < on at least one.
    Criteria (all "lower is better" after normalization):
    - total_paise: lower is better
    - shipping_days: lower is better
    - -warranty_months: more warranty is better (negated)
    - -return_window_days: more return window is better (negated)

    Complexity: O(k) where k = number of criteria (fixed = 4).
    """
    criteria_a = (a.total_paise, a.shipping_days, -a.warranty_months, -a.return_window_days)
    criteria_b = (b.total_paise, b.shipping_days, -b.warranty_months, -b.return_window_days)

    at_least_one_better = False
    for va, vb in zip(criteria_a, criteria_b):
        if va > vb:
            return False  # A is worse on this criterion
        if va < vb:
            at_least_one_better = True

    return at_least_one_better


def prune_dominated(offers: list[NegotiationOffer]) -> tuple[list[NegotiationOffer], list[NegotiationOffer]]:
    """
    Remove dominated offers from the candidate set.

    Returns (surviving, pruned) offers.

    Complexity: O(n²) pairwise comparison, but n is bounded by
    MAX_OFFERS_PER_ROUND × MAX_MERCHANTS (typically ≤ 30).
    Space: O(n).
    """
    if len(offers) <= 1:
        return list(offers), []

    surviving: list[NegotiationOffer] = []
    pruned: list[NegotiationOffer] = []

    for i, candidate in enumerate(offers):
        dominated = False
        for j, other in enumerate(offers):
            if i != j and offer_dominates(other, candidate):
                dominated = True
                break
        if dominated:
            pruned.append(candidate)
        else:
            surviving.append(candidate)

    return surviving, pruned


def filter_by_constraints(
    offers: list[NegotiationOffer],
    constraints: NegotiationConstraints,
) -> tuple[list[NegotiationOffer], list[NegotiationOffer]]:
    """
    Filter offers against user constraints.
    Returns (passing, rejected) offers.

    Complexity: O(n · c) where c = number of constraints (fixed ~ 5).
    """
    passing: list[NegotiationOffer] = []
    rejected: list[NegotiationOffer] = []

    for offer in offers:
        if offer.total_paise > constraints.max_total_paise:
            rejected.append(offer)
            continue
        if offer.warranty_months < constraints.min_warranty_months:
            rejected.append(offer)
            continue
        if offer.shipping_days > constraints.max_shipping_days:
            rejected.append(offer)
            continue
        if constraints.require_returnable and not offer.returnable:
            rejected.append(offer)
            continue
        if offer.return_window_days < constraints.min_return_window_days:
            rejected.append(offer)
            continue
        passing.append(offer)

    return passing, rejected


def rank_offers(offers: list[NegotiationOffer]) -> list[NegotiationOffer]:
    """
    Deterministic ranking: lowest total → shortest shipping → best warranty.

    Complexity: O(n log n) sort.
    """
    return sorted(
        offers,
        key=lambda o: (o.total_paise, o.shipping_days, -o.warranty_months),
    )


# ═══════════════════════════════════════════════════════
# Negotiation Session
# ═══════════════════════════════════════════════════════

MAX_ROUNDS = 5
MAX_MERCHANTS = 10
MAX_OFFERS_PER_ROUND = 10
MAX_NEGOTIATION_SECONDS = 120


@dataclass(slots=True)
class NegotiationRound:
    """Record of one negotiation round."""
    round_number: int
    offers_received: list[NegotiationOffer] = field(default_factory=list)
    constraint_filtered: list[NegotiationOffer] = field(default_factory=list)
    dominance_pruned: list[NegotiationOffer] = field(default_factory=list)
    surviving: list[NegotiationOffer] = field(default_factory=list)
    ranked: list[NegotiationOffer] = field(default_factory=list)
    elapsed_ms: float = 0.0


@dataclass(slots=True)
class NegotiationSession:
    """
    Complete negotiation session with bounded rounds.

    The session evaluates offers through:
    1. Constraint filtering (user constraints)
    2. Dominance pruning (Pareto)
    3. Deterministic ranking

    Complexity per round: O(n² + n log n) where n = offers
    Total: O(r · (n² + n log n)) bounded by MAX_ROUNDS × MAX_OFFERS
    Space: O(r · n) for round history
    """
    negotiation_id: UUID = field(default_factory=uuid4)
    constraints: NegotiationConstraints | None = None
    status: NegotiationStatus = NegotiationStatus.OPEN
    rounds: list[NegotiationRound] = field(default_factory=list)
    best_offer: NegotiationOffer | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def evaluate_round(
        self,
        offers: list[NegotiationOffer],
    ) -> NegotiationRound:
        """
        Process one round of negotiation.

        1. Validate round limits
        2. Filter by user constraints
        3. Dominance pruning
        4. Rank surviving offers

        Returns the round result with full transparency.
        """
        start = time.perf_counter()

        round_num = len(self.rounds) + 1
        if round_num > MAX_ROUNDS:
            raise ValueError(f"Maximum rounds ({MAX_ROUNDS}) exceeded")

        if len(offers) > MAX_OFFERS_PER_ROUND * MAX_MERCHANTS:
            raise ValueError(
                f"Too many offers: {len(offers)} > "
                f"{MAX_OFFERS_PER_ROUND * MAX_MERCHANTS}"
            )

        # Step 1: Constraint filtering
        if self.constraints:
            passing, rejected = filter_by_constraints(offers, self.constraints)
        else:
            passing, rejected = list(offers), []

        # Step 2: Dominance pruning
        surviving, pruned = prune_dominated(passing)

        # Step 3: Deterministic ranking
        ranked = rank_offers(surviving)

        elapsed_ms = (time.perf_counter() - start) * 1000

        round_result = NegotiationRound(
            round_number=round_num,
            offers_received=list(offers),
            constraint_filtered=rejected,
            dominance_pruned=pruned,
            surviving=surviving,
            ranked=ranked,
            elapsed_ms=round(elapsed_ms, 2),
        )

        self.rounds.append(round_result)

        # Update best offer
        if ranked:
            self.best_offer = ranked[0]

        return round_result

    def accept_best(self) -> NegotiationOffer | None:
        """Accept the current best offer. O(1)."""
        if self.best_offer is None:
            return None
        self.status = NegotiationStatus.ACCEPTED
        return self.best_offer

    def timeout(self) -> None:
        """Mark negotiation as timed out. O(1)."""
        self.status = NegotiationStatus.TIMEOUT

    def cancel(self) -> None:
        """Cancel negotiation. O(1)."""
        self.status = NegotiationStatus.CANCELLED
