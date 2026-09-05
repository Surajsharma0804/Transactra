"""
Transactra — Commerce State Machine and Order/Payment Tests

Validates:
- Cart state machine transitions
- Order state machine transitions
- Payment dual-state architecture (local vs provider)
- Payment.is_paid() requires provider confirmation
- Reconciliation detection
- Terminal state enforcement

All O(1) — no DB, no network.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from backend.kernel.domain.commerce_states import (
    CART_SM, ORDER_SM, PAYMENT_LOCAL_SM, PROVIDER_CONFIRMED_STATES,
)
from backend.kernel.domain.order import (
    Order, OrderStatus,
    Payment, PaymentLocalState, PaymentProviderState,
)


# ═══════════════════════════════════════════════════════
# Cart State Machine
# ═══════════════════════════════════════════════════════

class TestCartStateMachine:

    def test_happy_path(self) -> None:
        """Full cart lifecycle: open → priced → consent → authorized → paid."""
        state = "open"

        r = CART_SM.transition(state, "price")
        assert r.allowed and r.next_state == "priced"

        r = CART_SM.transition(r.next_state, "request_consent")
        assert r.allowed and r.next_state == "consent_pending"

        r = CART_SM.transition(r.next_state, "approve")
        assert r.allowed and r.next_state == "authorized"

        r = CART_SM.transition(r.next_state, "submit_payment")
        assert r.allowed and r.next_state == "payment_pending"

        r = CART_SM.transition(r.next_state, "payment_confirmed")
        assert r.allowed and r.next_state == "paid"

    def test_consent_rejected(self) -> None:
        r = CART_SM.transition("consent_pending", "reject")
        assert r.allowed and r.next_state == "cancelled"

    def test_consent_timeout(self) -> None:
        r = CART_SM.transition("consent_pending", "timeout")
        assert r.allowed and r.next_state == "expired"

    def test_payment_failed_returns_to_authorized(self) -> None:
        r = CART_SM.transition("payment_pending", "payment_failed")
        assert r.allowed and r.next_state == "authorized"

    def test_cancel_from_open(self) -> None:
        r = CART_SM.transition("open", "cancel")
        assert r.allowed and r.next_state == "cancelled"

    def test_cancel_from_authorized(self) -> None:
        r = CART_SM.transition("authorized", "cancel")
        assert r.allowed and r.next_state == "cancelled"

    def test_paid_is_terminal(self) -> None:
        assert CART_SM.is_terminal("paid")
        r = CART_SM.transition("paid", "cancel")
        assert not r.allowed

    def test_invalid_transition(self) -> None:
        r = CART_SM.transition("open", "approve")
        assert not r.allowed


# ═══════════════════════════════════════════════════════
# Order State Machine
# ═══════════════════════════════════════════════════════

class TestOrderStateMachine:

    def test_happy_path(self) -> None:
        state = "created"

        r = ORDER_SM.transition(state, "payment_initiated")
        assert r.allowed and r.next_state == "payment_pending"

        r = ORDER_SM.transition(r.next_state, "payment_confirmed")
        assert r.allowed and r.next_state == "paid"

        r = ORDER_SM.transition(r.next_state, "start_fulfillment")
        assert r.allowed and r.next_state == "fulfilling"

        r = ORDER_SM.transition(r.next_state, "ship")
        assert r.allowed and r.next_state == "shipped"

        r = ORDER_SM.transition(r.next_state, "deliver")
        assert r.allowed and r.next_state == "delivered"

    def test_payment_failure_and_retry(self) -> None:
        r = ORDER_SM.transition("payment_pending", "payment_failed")
        assert r.allowed and r.next_state == "payment_failed"

        r = ORDER_SM.transition(r.next_state, "retry_payment")
        assert r.allowed and r.next_state == "payment_pending"

    def test_refund_from_paid(self) -> None:
        r = ORDER_SM.transition("paid", "refund")
        assert r.allowed and r.next_state == "refunded"

    def test_refund_from_delivered(self) -> None:
        r = ORDER_SM.transition("delivered", "refund")
        assert r.allowed and r.next_state == "refunded"

    def test_refunded_is_terminal(self) -> None:
        assert ORDER_SM.is_terminal("refunded")
        assert ORDER_SM.is_terminal("cancelled")
        assert not ORDER_SM.is_terminal("delivered")  # refund still possible


# ═══════════════════════════════════════════════════════
# Payment State Machine (Local)
# ═══════════════════════════════════════════════════════

class TestPaymentLocalStateMachine:

    def test_happy_path(self) -> None:
        state = "initiated"

        r = PAYMENT_LOCAL_SM.transition(state, "send_to_provider")
        assert r.allowed and r.next_state == "provider_requested"

        r = PAYMENT_LOCAL_SM.transition(r.next_state, "provider_ack")
        assert r.allowed and r.next_state == "provider_acknowledged"

        r = PAYMENT_LOCAL_SM.transition(r.next_state, "webhook_success")
        assert r.allowed and r.next_state == "completed"

    def test_provider_error_and_retry(self) -> None:
        r = PAYMENT_LOCAL_SM.transition("provider_requested", "provider_error")
        assert r.allowed and r.next_state == "provider_error"

        r = PAYMENT_LOCAL_SM.transition(r.next_state, "retry")
        assert r.allowed and r.next_state == "provider_requested"

    def test_timeout_reconciliation(self) -> None:
        r = PAYMENT_LOCAL_SM.transition("provider_acknowledged", "timeout")
        assert r.allowed and r.next_state == "timeout"

        # Reconciliation resolves the timeout
        r_ok = PAYMENT_LOCAL_SM.transition("timeout", "reconcile_success")
        assert r_ok.allowed and r_ok.next_state == "completed"

        r_fail = PAYMENT_LOCAL_SM.transition("timeout", "reconcile_failure")
        assert r_fail.allowed and r_fail.next_state == "failed"

    def test_abandon_from_error(self) -> None:
        r = PAYMENT_LOCAL_SM.transition("provider_error", "abandon")
        assert r.allowed and r.next_state == "abandoned"

    def test_completed_is_terminal(self) -> None:
        assert PAYMENT_LOCAL_SM.is_terminal("completed")
        assert PAYMENT_LOCAL_SM.is_terminal("failed")
        assert PAYMENT_LOCAL_SM.is_terminal("abandoned")


# ═══════════════════════════════════════════════════════
# Payment Dual-State Domain Type
# ═══════════════════════════════════════════════════════

class TestPaymentDualState:

    def test_is_paid_requires_provider_confirmation(self) -> None:
        """INV-09: Only provider webhook can confirm paid."""
        # Local state says completed, but no provider confirmation
        p = Payment(
            payment_id=uuid4(), order_id=uuid4(),
            amount_paise=6_800_000,
            local_state=PaymentLocalState.COMPLETED,
            provider_confirmed_state=None,
        )
        assert not p.is_paid()  # NOT paid without provider confirmation

    def test_is_paid_with_provider_capture(self) -> None:
        p = Payment(
            payment_id=uuid4(), order_id=uuid4(),
            amount_paise=6_800_000,
            local_state=PaymentLocalState.COMPLETED,
            provider_confirmed_state=PaymentProviderState.CAPTURED,
        )
        assert p.is_paid()

    def test_is_failed_with_provider(self) -> None:
        p = Payment(
            payment_id=uuid4(), order_id=uuid4(),
            amount_paise=6_800_000,
            provider_confirmed_state=PaymentProviderState.FAILED,
        )
        assert p.is_failed()

    def test_needs_reconciliation_requested(self) -> None:
        p = Payment(
            payment_id=uuid4(), order_id=uuid4(),
            amount_paise=6_800_000,
            local_state=PaymentLocalState.PROVIDER_REQUESTED,
            provider_confirmed_state=None,
        )
        assert p.needs_reconciliation()

    def test_needs_reconciliation_timeout(self) -> None:
        p = Payment(
            payment_id=uuid4(), order_id=uuid4(),
            amount_paise=6_800_000,
            local_state=PaymentLocalState.TIMEOUT,
            provider_confirmed_state=None,
        )
        assert p.needs_reconciliation()

    def test_no_reconciliation_when_confirmed(self) -> None:
        p = Payment(
            payment_id=uuid4(), order_id=uuid4(),
            amount_paise=6_800_000,
            local_state=PaymentLocalState.COMPLETED,
            provider_confirmed_state=PaymentProviderState.CAPTURED,
        )
        assert not p.needs_reconciliation()

    def test_zero_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            Payment(payment_id=uuid4(), order_id=uuid4(), amount_paise=0)

    def test_frozen(self) -> None:
        p = Payment(payment_id=uuid4(), order_id=uuid4(), amount_paise=6_800_000)
        with pytest.raises(AttributeError):
            p.amount_paise = 0  # type: ignore[misc]
