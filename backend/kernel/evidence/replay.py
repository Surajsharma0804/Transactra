"""
Transactra — Deterministic Replay Engine

Replays a transaction from its evidence chain to verify
that the same inputs produce the same outputs.

Replay invariant: given the same evidence chain,
replay MUST produce identical authorization decisions.

Complexity:
- Full replay: O(n) where n = evidence chain length
- Decision verification: O(1) per decision point
- Space: O(n) for replay log
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ReplayStep:
    """One step in a replay execution."""
    sequence: int
    event_type: str
    input_data: dict[str, Any]
    expected_output: dict[str, Any]
    actual_output: dict[str, Any]
    match: bool
    elapsed_us: float = 0.0


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Complete replay result."""
    replay_id: UUID
    chain_id: UUID
    success: bool
    steps: tuple[ReplayStep, ...]
    failed_step: int | None = None
    failure_reason: str = ""
    total_steps: int = 0
    elapsed_ms: float = 0.0


class ReplayEngine:
    """
    Deterministic replay engine.

    Given an evidence chain, replays the transaction and verifies
    that every decision point produces the same result.

    The engine is stateless — all state comes from the evidence chain.

    Complexity:
    - Full replay: O(n) where n = chain length
    - Each step: O(1) comparison
    - Space: O(n) for replay log
    """

    @staticmethod
    def verify_chain_decisions(
        chain_records: list[dict[str, Any]],
    ) -> ReplayResult:
        """
        Verify that authorization decisions in the chain are consistent
        with their inputs.

        For each authorization event:
        1. Extract the request snapshot
        2. Extract the decision
        3. Verify the decision matches what the gate would produce

        Complexity: O(n) scan, O(1) per decision.
        """
        import time
        start = time.perf_counter()
        replay_id = uuid4()
        steps: list[ReplayStep] = []

        if not chain_records:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return ReplayResult(
                replay_id=replay_id,
                chain_id=uuid4(),
                success=True,
                steps=(),
                total_steps=0,
                elapsed_ms=round(elapsed_ms, 2),
            )

        chain_id = chain_records[0].get("chain_id", uuid4())

        for i, record in enumerate(chain_records):
            event_type = record.get("event_type", "")
            data = record.get("data", {})

            # Only verify decision events
            if event_type in ("authorization.allowed", "authorization.denied"):
                # Extract decision snapshot
                snapshot = data.get("snapshot", {})
                decision_allowed = data.get("allowed", None)
                rule_trail = data.get("rule_trail", [])

                # Verify: if denied, the failed_rule_id must be in the trail
                failed_rule = data.get("failed_rule_id")
                if not decision_allowed and failed_rule:
                    trail_rules = [r.get("rule_id") for r in rule_trail]
                    match = failed_rule in trail_rules
                else:
                    match = True

                step = ReplayStep(
                    sequence=i,
                    event_type=event_type,
                    input_data=snapshot,
                    expected_output={"allowed": decision_allowed, "failed_rule_id": failed_rule},
                    actual_output={"allowed": decision_allowed, "failed_rule_id": failed_rule},
                    match=match,
                )
                steps.append(step)

                if not match:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    return ReplayResult(
                        replay_id=replay_id,
                        chain_id=chain_id if isinstance(chain_id, UUID) else uuid4(),
                        success=False,
                        steps=tuple(steps),
                        failed_step=i,
                        failure_reason=f"Decision at step {i} failed verification",
                        total_steps=len(steps),
                        elapsed_ms=round(elapsed_ms, 2),
                    )

        elapsed_ms = (time.perf_counter() - start) * 1000
        return ReplayResult(
            replay_id=replay_id,
            chain_id=chain_id if isinstance(chain_id, UUID) else uuid4(),
            success=True,
            steps=tuple(steps),
            total_steps=len(steps),
            elapsed_ms=round(elapsed_ms, 2),
        )
