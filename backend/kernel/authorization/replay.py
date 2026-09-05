"""
Transactra — Counterfactual Replay Engine

Re-runs authorization decisions with modified inputs to answer
"what if?" questions:

- "What if the budget was ₹5,000 instead of ₹10,000?"
- "What if the merchant was not in the allowed list?"
- "What if the mandate had expired?"

This is NOT just a self-consistency check. It:
1. Loads the original decision's snapshot
2. Overrides specified predicate inputs
3. Re-runs the REAL 16-predicate gate with modified values
4. Returns the new decision + a diff showing which predicates changed

Complexity: O(1) per replay (gate evaluation is O(1)).
Space: O(16) for rule trail (fixed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from backend.kernel.authorization.gate import (
    AuthorizationGate,
    AuthorizationRequest,
    AuthorizationDecision,
    PredicateResult,
)


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """
    Result of a counterfactual replay.

    Contains both the original and replayed decisions,
    plus a diff showing which predicates changed outcome.
    """
    original_decision_id: UUID
    replay_decision_id: UUID
    original_allowed: bool
    replay_allowed: bool
    outcome_changed: bool
    overrides_applied: dict[str, Any]
    predicate_diffs: tuple[PredicateDiff, ...]
    replayed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class PredicateDiff:
    """Shows how a single predicate's result changed in the replay."""
    rule_id: str
    original_passed: bool
    replay_passed: bool
    changed: bool


class ReplayEngine:
    """
    Counterfactual replay engine for authorization decisions.

    Takes a stored decision, applies user-specified overrides to
    the predicate inputs, and re-evaluates the gate from scratch.

    This is real counterfactual analysis — not just checking if the
    logged answer is internally consistent.

    Space: O(d) where d = number of stored decisions.
    """

    def __init__(self) -> None:
        self._gate = AuthorizationGate()

    def replay(
        self,
        original_decision: AuthorizationDecision,
        original_inputs: dict[str, Any],
        overrides: dict[str, Any],
    ) -> ReplayResult:
        """
        Re-run the authorization gate with modified inputs.

        Args:
            original_decision: The original AuthorizationDecision to replay
            original_inputs: The resolved predicate inputs from the original run
            overrides: Dict of input names to override values
                       e.g. {"mandate_has_budget": False, "amount_paise": 500000}

        Returns:
            ReplayResult with full diff analysis

        Complexity: O(1) — gate evaluation is O(1).
        """
        # Merge original inputs with overrides
        replayed_inputs = {**original_inputs, **overrides}

        # Rebuild the AuthorizationRequest (may have amount override)
        original_req = original_decision.request_id
        request = AuthorizationRequest(
            request_id=uuid4(),
            principal_user_id=replayed_inputs.get("principal_user_id", uuid4()),
            agent_id=replayed_inputs.get("agent_id", uuid4()),
            mandate_id=replayed_inputs.get("mandate_id", uuid4()),
            consent_id=replayed_inputs.get("consent_id", uuid4()),
            cart_hash=replayed_inputs.get("cart_hash", "replay"),
            amount_paise=replayed_inputs.get("amount_paise", 100),
            currency=replayed_inputs.get("currency", "INR"),
            category=replayed_inputs.get("category", ""),
            merchant_id=replayed_inputs.get("merchant_id", uuid4()),
            idempotency_key=f"replay-{uuid4()}",
            authorization_nonce=f"replay-{uuid4()}",
        )

        # Re-run the REAL gate with potentially modified inputs
        replay_decision = self._gate.evaluate(
            request,
            principal_active=replayed_inputs.get("principal_active", True),
            principal_user_id=request.principal_user_id,
            agent_active=replayed_inputs.get("agent_active", True),
            agent_owner_id=replayed_inputs.get("agent_owner_id", request.principal_user_id),
            agent_capabilities=frozenset(replayed_inputs.get("agent_capabilities", {"request_authorization"})),
            mandate_active=replayed_inputs.get("mandate_active", True),
            mandate_owner_id=replayed_inputs.get("mandate_owner_id", request.principal_user_id),
            mandate_agent_id=replayed_inputs.get("mandate_agent_id", request.agent_id),
            mandate_has_budget=replayed_inputs.get("mandate_has_budget", True),
            mandate_category_ok=replayed_inputs.get("mandate_category_ok", True),
            mandate_merchant_ok=replayed_inputs.get("mandate_merchant_ok", True),
            mandate_cart_hash=replayed_inputs.get("mandate_cart_hash", None),
            consent_valid=replayed_inputs.get("consent_valid", True),
            consent_cart_hash=replayed_inputs.get("consent_cart_hash", request.cart_hash),
            nonce_unused=True,  # Always fresh for replay
            idempotency_fresh=True,  # Always fresh for replay
        )

        # Build predicate-level diff
        original_trail = {r.rule_id: r for r in original_decision.rule_trail}
        replay_trail = {r.rule_id: r for r in replay_decision.rule_trail}

        diffs = []
        all_rule_ids = sorted(set(list(original_trail.keys()) + list(replay_trail.keys())))
        for rule_id in all_rule_ids:
            orig = original_trail.get(rule_id)
            repl = replay_trail.get(rule_id)
            orig_passed = orig.passed if orig else True  # Not reached = would have passed
            repl_passed = repl.passed if repl else True
            diffs.append(PredicateDiff(
                rule_id=rule_id,
                original_passed=orig_passed,
                replay_passed=repl_passed,
                changed=orig_passed != repl_passed,
            ))

        return ReplayResult(
            original_decision_id=original_decision.decision_id,
            replay_decision_id=replay_decision.decision_id,
            original_allowed=original_decision.allowed,
            replay_allowed=replay_decision.allowed,
            outcome_changed=original_decision.allowed != replay_decision.allowed,
            overrides_applied=overrides,
            predicate_diffs=tuple(diffs),
        )
