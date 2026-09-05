"""
Transactra — Generic Deterministic State Machine

O(1) transition lookup via dict. Used for Cart, Order, Payment, Negotiation.
All transitions are guarded and logged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

S = TypeVar("S", bound=str)
E = TypeVar("E", bound=str)


@dataclass(frozen=True, slots=True)
class TransitionResult(Generic[S]):
    """Result of a state transition attempt."""
    allowed: bool
    next_state: S | None = None
    rule_id: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class TransitionRule(Generic[S]):
    """
    A transition rule: event in current state → target state, guarded.

    guard: callable(context) -> bool.  If None, always passes.
    guard_failure_reason: human-readable explanation.
    """
    target: S
    rule_id: str
    guard: Callable[[dict[str, Any]], bool] | None = None
    guard_failure_reason: str = ""


class StateMachine(Generic[S, E]):
    """
    Generic deterministic state machine.

    Transition lookup: O(1) via dict[(current_state, event)].
    Guard evaluation: O(g) where g = cost of guard function (typically O(1)).
    Space: O(T) where T = number of registered transitions.

    Invariant: Every transition is deterministic and auditable.
    """

    def __init__(
        self,
        name: str,
        transitions: dict[tuple[S, E], TransitionRule[S]],
        terminal_states: frozenset[S] | None = None,
    ) -> None:
        self._name = name
        self._transitions = transitions
        self._terminal_states = terminal_states or frozenset()

    def can_transition(self, current: S, event: E) -> bool:
        """Check if a transition is registered (ignores guard). O(1)."""
        return (current, event) in self._transitions

    def is_terminal(self, state: S) -> bool:
        """Check if state is terminal. O(1)."""
        return state in self._terminal_states

    def transition(
        self,
        current: S,
        event: E,
        context: dict[str, Any] | None = None,
    ) -> TransitionResult[S]:
        """
        Attempt a state transition.

        Returns TransitionResult with allowed=True and next_state on success,
        or allowed=False with rule_id and reason on failure.

        Complexity: O(1) lookup + O(g) guard evaluation.
        """
        if self.is_terminal(current):
            return TransitionResult(
                allowed=False,
                rule_id="TERMINAL_STATE",
                reason=f"State '{current}' is terminal in {self._name}",
            )

        key = (current, event)
        rule = self._transitions.get(key)

        if rule is None:
            return TransitionResult(
                allowed=False,
                rule_id="STATE_TRANSITION_INVALID",
                reason=f"No transition from '{current}' on '{event}' in {self._name}",
            )

        if rule.guard is not None:
            ctx = context or {}
            try:
                if not rule.guard(ctx):
                    return TransitionResult(
                        allowed=False,
                        rule_id=rule.rule_id,
                        reason=rule.guard_failure_reason or f"Guard failed for {rule.rule_id}",
                    )
            except Exception as e:
                # Fail closed
                return TransitionResult(
                    allowed=False,
                    rule_id=rule.rule_id,
                    reason=f"Guard error: {e}",
                )

        return TransitionResult(
            allowed=True,
            next_state=rule.target,
            rule_id=rule.rule_id,
        )

    def get_valid_events(self, current: S) -> list[E]:
        """List all events valid from current state. O(T) worst, typically small."""
        return [event for (state, event) in self._transitions if state == current]

    @property
    def name(self) -> str:
        return self._name
