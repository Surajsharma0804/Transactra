"""
Transactra — Trust Evidence Engine

Computes merchant trust scores from real transaction data.
Trust is not self-declared — it is computed from evidence:

- Order completion rate (delivered / total orders)
- On-time delivery rate (within shipping_days commitment)
- Dispute rate (disputes / total orders)
- Evidence chain integrity (all chains verified)
- Average fulfillment time

Trust score range: 0.0 to 1.0 (1.0 = perfect trust)

Complexity:
- compute_trust_score: O(n) where n = merchant's order count
- TrustEvidence construction: O(1)
- update_on_order_complete: O(1) amortized
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TrustEvidence:
    """
    Immutable trust evidence record for a merchant.

    Computed from real order data — not self-declared.
    Every field has a clear evidence source.
    """
    merchant_id: UUID
    total_orders: int
    completed_orders: int
    on_time_deliveries: int
    disputes: int
    avg_fulfillment_hours: float
    evidence_chains_verified: int
    evidence_chains_broken: int
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def fulfillment_rate(self) -> float:
        """Fraction of orders successfully completed. O(1)."""
        if self.total_orders == 0:
            return 0.0
        return self.completed_orders / self.total_orders

    @property
    def on_time_rate(self) -> float:
        """Fraction of completed orders delivered on time. O(1)."""
        if self.completed_orders == 0:
            return 0.0
        return self.on_time_deliveries / self.completed_orders

    @property
    def dispute_rate(self) -> float:
        """Fraction of orders with disputes. O(1). Lower is better."""
        if self.total_orders == 0:
            return 0.0
        return self.disputes / self.total_orders

    @property
    def chain_integrity_rate(self) -> float:
        """Fraction of evidence chains that pass verification. O(1)."""
        total_chains = self.evidence_chains_verified + self.evidence_chains_broken
        if total_chains == 0:
            return 1.0  # No chains to verify = no evidence of tampering
        return self.evidence_chains_verified / total_chains

    @property
    def trust_score(self) -> float:
        """
        Composite trust score: 0.0 to 1.0.

        Weighted formula:
        - 40% fulfillment rate (most important: did they deliver?)
        - 25% on-time delivery (did they deliver when promised?)
        - 20% dispute rate (inverted: fewer disputes = higher trust)
        - 15% chain integrity (is the evidence tamper-free?)

        O(1) computation.
        """
        score = (
            0.40 * self.fulfillment_rate
            + 0.25 * self.on_time_rate
            + 0.20 * (1.0 - self.dispute_rate)
            + 0.15 * self.chain_integrity_rate
        )
        return round(min(1.0, max(0.0, score)), 4)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for API response. O(1)."""
        return {
            "merchant_id": str(self.merchant_id),
            "trust_score": self.trust_score,
            "fulfillment_rate": round(self.fulfillment_rate, 4),
            "on_time_rate": round(self.on_time_rate, 4),
            "dispute_rate": round(self.dispute_rate, 4),
            "chain_integrity_rate": round(self.chain_integrity_rate, 4),
            "total_orders": self.total_orders,
            "completed_orders": self.completed_orders,
            "computed_at": self.computed_at.isoformat() + "Z",
        }


class TrustEngine:
    """
    Computes and caches merchant trust scores.

    In-memory aggregation from order data.
    Production would use materialized views or periodic batch computation.

    Space: O(m) where m = number of merchants.
    """

    def __init__(self) -> None:
        # Merchant-level accumulators — O(1) per update
        self._stats: dict[UUID, dict[str, int | float]] = {}

    def _ensure_merchant(self, merchant_id: UUID) -> dict[str, int | float]:
        """Lazy-init merchant stats. O(1)."""
        if merchant_id not in self._stats:
            self._stats[merchant_id] = {
                "total_orders": 0,
                "completed_orders": 0,
                "on_time_deliveries": 0,
                "disputes": 0,
                "total_fulfillment_hours": 0.0,
                "evidence_chains_verified": 0,
                "evidence_chains_broken": 0,
            }
        return self._stats[merchant_id]

    def record_order_created(self, merchant_id: UUID) -> None:
        """Record a new order for a merchant. O(1)."""
        stats = self._ensure_merchant(merchant_id)
        stats["total_orders"] += 1

    def record_order_completed(
        self,
        merchant_id: UUID,
        fulfillment_hours: float,
        was_on_time: bool,
    ) -> None:
        """Record a successfully completed order. O(1)."""
        stats = self._ensure_merchant(merchant_id)
        stats["completed_orders"] += 1
        stats["total_fulfillment_hours"] += fulfillment_hours
        if was_on_time:
            stats["on_time_deliveries"] += 1

    def record_dispute(self, merchant_id: UUID) -> None:
        """Record a dispute against a merchant. O(1)."""
        stats = self._ensure_merchant(merchant_id)
        stats["disputes"] += 1

    def record_chain_verification(
        self, merchant_id: UUID, passed: bool
    ) -> None:
        """Record evidence chain verification result. O(1)."""
        stats = self._ensure_merchant(merchant_id)
        if passed:
            stats["evidence_chains_verified"] += 1
        else:
            stats["evidence_chains_broken"] += 1

    def compute_trust(self, merchant_id: UUID) -> TrustEvidence:
        """
        Compute trust evidence for a merchant. O(1).

        Returns a frozen, immutable TrustEvidence record.
        """
        stats = self._ensure_merchant(merchant_id)
        completed = int(stats["completed_orders"])
        avg_hours = (
            float(stats["total_fulfillment_hours"]) / completed
            if completed > 0
            else 0.0
        )

        return TrustEvidence(
            merchant_id=merchant_id,
            total_orders=int(stats["total_orders"]),
            completed_orders=completed,
            on_time_deliveries=int(stats["on_time_deliveries"]),
            disputes=int(stats["disputes"]),
            avg_fulfillment_hours=round(avg_hours, 2),
            evidence_chains_verified=int(stats["evidence_chains_verified"]),
            evidence_chains_broken=int(stats["evidence_chains_broken"]),
        )

    def get_all_trust_scores(self) -> list[TrustEvidence]:
        """
        Compute trust scores for all known merchants.

        O(m) where m = number of merchants.
        """
        return [self.compute_trust(mid) for mid in self._stats]


# Module-level singleton — shared across the application
_trust_engine = TrustEngine()


def get_trust_engine() -> TrustEngine:
    """Get the shared trust engine instance. O(1)."""
    return _trust_engine
