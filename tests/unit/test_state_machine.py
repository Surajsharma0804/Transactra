"""
Transactra — State Machine Tests

Validates:
- O(1) transition lookup
- Guard evaluation
- Terminal state enforcement
- Invalid transition rejection
- Fail-closed on guard errors
"""

from __future__ import annotations

import pytest

from backend.kernel.domain.state_machine import StateMachine, TransitionRule, TransitionResult


def _always_true(ctx: dict) -> bool:
    return True


def _always_false(ctx: dict) -> bool:
    return False


def _check_stock(ctx: dict) -> bool:
    return ctx.get("stock", 0) > 0


def _raise_error(ctx: dict) -> bool:
    raise RuntimeError("Simulated guard failure")


# Build a simple test state machine
def _build_cart_sm() -> StateMachine[str, str]:
    return StateMachine(
        name="cart",
        transitions={
            ("open", "price_cart"): TransitionRule(
                target="priced", rule_id="CART_PRICE",
            ),
            ("priced", "request_consent"): TransitionRule(
                target="consent_pending", rule_id="CART_CONSENT",
                guard=_check_stock,
                guard_failure_reason="Out of stock",
            ),
            ("consent_pending", "user_approves"): TransitionRule(
                target="authorized", rule_id="CART_AUTHORIZE",
            ),
            ("consent_pending", "timeout"): TransitionRule(
                target="expired", rule_id="CART_EXPIRE",
            ),
            ("open", "timeout"): TransitionRule(
                target="expired", rule_id="CART_EXPIRE",
            ),
        },
        terminal_states=frozenset({"expired", "cancelled"}),
    )


class TestStateMachineTransitions:

    def test_valid_transition(self) -> None:
        sm = _build_cart_sm()
        result = sm.transition("open", "price_cart")
        assert result.allowed
        assert result.next_state == "priced"
        assert result.rule_id == "CART_PRICE"

    def test_chained_transitions(self) -> None:
        sm = _build_cart_sm()
        r1 = sm.transition("open", "price_cart")
        assert r1.allowed and r1.next_state == "priced"

        r2 = sm.transition(r1.next_state, "request_consent", {"stock": 5})
        assert r2.allowed and r2.next_state == "consent_pending"

        r3 = sm.transition(r2.next_state, "user_approves")
        assert r3.allowed and r3.next_state == "authorized"

    def test_invalid_transition(self) -> None:
        sm = _build_cart_sm()
        result = sm.transition("open", "user_approves")
        assert not result.allowed
        assert result.rule_id == "STATE_TRANSITION_INVALID"

    def test_terminal_state_blocks_transition(self) -> None:
        sm = _build_cart_sm()
        result = sm.transition("expired", "price_cart")
        assert not result.allowed
        assert result.rule_id == "TERMINAL_STATE"


class TestStateMachineGuards:

    def test_guard_passes(self) -> None:
        sm = _build_cart_sm()
        result = sm.transition("priced", "request_consent", {"stock": 3})
        assert result.allowed
        assert result.next_state == "consent_pending"

    def test_guard_fails(self) -> None:
        sm = _build_cart_sm()
        result = sm.transition("priced", "request_consent", {"stock": 0})
        assert not result.allowed
        assert "Out of stock" in result.reason

    def test_guard_error_fails_closed(self) -> None:
        """Fail closed: guard exception → DENY."""
        sm = StateMachine(
            name="test",
            transitions={
                ("a", "go"): TransitionRule(
                    target="b", rule_id="TEST",
                    guard=_raise_error,
                ),
            },
        )
        result = sm.transition("a", "go")
        assert not result.allowed
        assert "Guard error" in result.reason


class TestStateMachineMetadata:

    def test_can_transition_check(self) -> None:
        sm = _build_cart_sm()
        assert sm.can_transition("open", "price_cart")
        assert not sm.can_transition("open", "user_approves")

    def test_is_terminal(self) -> None:
        sm = _build_cart_sm()
        assert sm.is_terminal("expired")
        assert sm.is_terminal("cancelled")
        assert not sm.is_terminal("open")

    def test_get_valid_events(self) -> None:
        sm = _build_cart_sm()
        events = sm.get_valid_events("open")
        assert "price_cart" in events
        assert "timeout" in events
        assert "user_approves" not in events

    def test_name(self) -> None:
        sm = _build_cart_sm()
        assert sm.name == "cart"
