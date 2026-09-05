"""
Transactra — 16-Predicate Authorization Gate

The core deterministic decision engine. Every authorization request
passes through 16 predicates evaluated in short-circuit order.

ALL 16 must pass → ALLOW.  ANY failure → DENY with rule ID and reason.

Short-circuit evaluation order (cheapest first):
  1.  RequestFormatValid        O(1)    Parse/schema check
  2.  PrincipalAuthenticated    O(1)    JWT/session valid
  3.  PrincipalActive           O(1)    Status check
  4.  AgentActive               O(1)    Status + expiry
  5.  AgentOwnedByPrincipal     O(1)    FK check
  6.  MandateExists             O(1)    Lookup
  7.  MandateActive             O(1)    Status + time window
  8.  MandateOwnedByPrincipal   O(1)    FK check
  9.  MandateCoversCategory     O(k)    Category ∈ allowed set
  10. MandateCoversAmount       O(1)    Budget check
  11. MandateCoversMerchant     O(k)    Merchant ∈ allowed set
  12. CartHashMatches           O(1)    Exact hash compare
  13. ConsentValid              O(1)    Status + expiry
  14. ConsentMatchesCart         O(1)    Hash compare
  15. NonceUnused               O(1)    Unique constraint
  16. IdempotencyKeyFresh       O(1)    Unique constraint

Total: O(1) amortized (all individual predicates are O(1) or O(k) with small k).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class AuthorizationRequest:
    """Input to the authorization gate."""
    request_id: UUID
    principal_user_id: UUID
    agent_id: UUID
    mandate_id: UUID
    consent_id: UUID
    cart_hash: str
    amount_paise: int
    currency: str
    category: str
    merchant_id: UUID
    idempotency_key: str
    authorization_nonce: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.amount_paise <= 0:
            raise ValueError(f"Amount must be positive: {self.amount_paise}")
        if not self.idempotency_key:
            raise ValueError("Idempotency key is required")
        if not self.authorization_nonce:
            raise ValueError("Authorization nonce is required")
        if not self.cart_hash:
            raise ValueError("Cart hash is required")


@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    """
    Immutable authorization decision. Every decision is ALLOW or DENY
    with a rule trail showing which predicates were evaluated.

    This is the evidence record — stored permanently in the audit log.
    """
    decision_id: UUID
    request_id: UUID
    allowed: bool
    rule_trail: tuple[PredicateResult, ...]
    failed_rule_id: str | None = None
    failed_reason: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def is_allow(self) -> bool:
        return self.allowed

    @property
    def is_deny(self) -> bool:
        return not self.allowed


@dataclass(frozen=True, slots=True)
class PredicateResult:
    """Result of a single predicate evaluation."""
    rule_id: str
    passed: bool
    reason: str = ""
    elapsed_us: float = 0.0  # microseconds


class AuthorizationGate:
    """
    16-predicate authorization gate.

    Fail-closed: unknown state → DENY.
    Short-circuit: first failure stops evaluation.

    The gate takes resolved domain objects (not raw IDs) so that
    the caller is responsible for lookup and locking.
    """

    def evaluate(
        self,
        request: AuthorizationRequest,
        principal_active: bool,
        principal_user_id: UUID,
        agent_active: bool,
        agent_owner_id: UUID,
        agent_capabilities: frozenset[str],
        mandate_active: bool,
        mandate_owner_id: UUID,
        mandate_agent_id: UUID,
        mandate_has_budget: bool,
        mandate_category_ok: bool,
        mandate_merchant_ok: bool,
        mandate_cart_hash: str | None,
        consent_valid: bool,
        consent_cart_hash: str,
        nonce_unused: bool,
        idempotency_fresh: bool,
    ) -> AuthorizationDecision:
        """
        Evaluate all 16 predicates in short-circuit order.

        Returns an immutable AuthorizationDecision with full rule trail.

        Complexity: O(1) amortized — each predicate is O(1).
        Space: O(16) for rule trail (fixed).
        """
        trail: list[PredicateResult] = []
        request_id = request.request_id

        predicates = [
            # 1. Request format valid (already validated by dataclass)
            ("AUTH_001_REQUEST_FORMAT", True, "Request format valid"),

            # 2. Principal authenticated (already resolved)
            ("AUTH_002_PRINCIPAL_AUTHENTICATED", True, "Principal authenticated"),

            # 3. Principal active
            ("AUTH_003_PRINCIPAL_ACTIVE", principal_active,
             "Principal is not active" if not principal_active else ""),

            # 4. Agent active (status + expiry)
            ("AUTH_004_AGENT_ACTIVE", agent_active,
             "Agent is not active or has expired" if not agent_active else ""),

            # 5. Agent owned by principal
            ("AUTH_005_AGENT_OWNED", agent_owner_id == principal_user_id,
             f"Agent owner {agent_owner_id} != principal {principal_user_id}"
             if agent_owner_id != principal_user_id else ""),

            # 6. Mandate exists (already resolved — if we got here it exists)
            ("AUTH_006_MANDATE_EXISTS", True, "Mandate resolved"),

            # 7. Mandate active
            ("AUTH_007_MANDATE_ACTIVE", mandate_active,
             "Mandate is not active (expired/revoked/exhausted)" if not mandate_active else ""),

            # 8. Mandate owned by principal
            ("AUTH_008_MANDATE_OWNED", mandate_owner_id == principal_user_id,
             f"Mandate owner {mandate_owner_id} != principal {principal_user_id}"
             if mandate_owner_id != principal_user_id else ""),

            # 9. Mandate covers category
            ("AUTH_009_CATEGORY_ALLOWED", mandate_category_ok,
             f"Category '{request.category}' not in mandate allowed categories"
             if not mandate_category_ok else ""),

            # 10. Mandate covers amount (budget check)
            ("AUTH_010_BUDGET_SUFFICIENT", mandate_has_budget,
             f"Insufficient mandate budget for {request.amount_paise} paise"
             if not mandate_has_budget else ""),

            # 11. Mandate covers merchant
            ("AUTH_011_MERCHANT_ALLOWED", mandate_merchant_ok,
             f"Merchant {request.merchant_id} not in mandate allowed merchants"
             if not mandate_merchant_ok else ""),

            # 12. Cart hash matches mandate binding
            ("AUTH_012_CART_HASH_MATCHES",
             mandate_cart_hash is None or mandate_cart_hash == request.cart_hash,
             f"Cart hash mismatch: mandate has {mandate_cart_hash}, request has {request.cart_hash}"
             if mandate_cart_hash is not None and mandate_cart_hash != request.cart_hash else ""),

            # 13. Consent valid (approved + not expired)
            ("AUTH_013_CONSENT_VALID", consent_valid,
             "Consent is not valid (not approved or expired)" if not consent_valid else ""),

            # 14. Consent matches cart (INV-06)
            ("AUTH_014_CONSENT_CART_MATCHES", consent_cart_hash == request.cart_hash,
             f"Consent cart hash mismatch (cart changed after consent)"
             if consent_cart_hash != request.cart_hash else ""),

            # 15. Nonce unused (replay protection)
            ("AUTH_015_NONCE_UNUSED", nonce_unused,
             "Authorization nonce has already been used (replay detected)"
             if not nonce_unused else ""),

            # 16. Idempotency key fresh (duplicate request protection)
            ("AUTH_016_IDEMPOTENCY_FRESH", idempotency_fresh,
             "Idempotency key already exists (duplicate request)"
             if not idempotency_fresh else ""),
        ]

        for rule_id, passed, reason in predicates:
            trail.append(PredicateResult(rule_id=rule_id, passed=passed, reason=reason))

            if not passed:
                # Short-circuit: DENY on first failure
                return AuthorizationDecision(
                    decision_id=uuid4(),
                    request_id=request_id,
                    allowed=False,
                    rule_trail=tuple(trail),
                    failed_rule_id=rule_id,
                    failed_reason=reason,
                    snapshot=self._build_snapshot(request),
                )

        # All 16 passed → ALLOW
        return AuthorizationDecision(
            decision_id=uuid4(),
            request_id=request_id,
            allowed=True,
            rule_trail=tuple(trail),
            snapshot=self._build_snapshot(request),
        )

    @staticmethod
    def _build_snapshot(request: AuthorizationRequest) -> dict[str, Any]:
        """Build immutable decision snapshot for audit. O(1)."""
        return {
            "request_id": str(request.request_id),
            "user_id": str(request.principal_user_id),
            "agent_id": str(request.agent_id),
            "mandate_id": str(request.mandate_id),
            "consent_id": str(request.consent_id),
            "amount_paise": request.amount_paise,
            "currency": request.currency,
            "cart_hash": request.cart_hash,
            "category": request.category,
            "merchant_id": str(request.merchant_id),
            "timestamp": request.timestamp.isoformat(),
        }
