"""
Transactra — Order and Payment State Machine Definitions

Concrete state machines for the Commerce Kernel:
- Cart: open → priced → consent_pending → authorized → payment_pending → paid
- Order: created → payment_pending → paid → fulfilling → shipped → delivered
- Payment: initiated → provider_requested → (dual-state: local + provider_confirmed)

Payment uses dual-state architecture:
- local_state: what we did (initiated, requested, etc.)
- provider_confirmed_state: what the webhook confirmed (null until webhook)
- Only provider_confirmed_state is authoritative for "paid"

Complexity: All transitions are O(1) dict lookup.
"""

from __future__ import annotations

from backend.kernel.domain.state_machine import StateMachine, TransitionRule


# ═══════════════════════════════════════════════════════
# Cart State Machine
# ═══════════════════════════════════════════════════════

CART_SM = StateMachine(
    name="cart",
    transitions={
        ("open", "price"): TransitionRule(target="priced", rule_id="CART_001_PRICE"),
        ("priced", "request_consent"): TransitionRule(target="consent_pending", rule_id="CART_002_CONSENT"),
        ("consent_pending", "approve"): TransitionRule(target="authorized", rule_id="CART_003_APPROVE"),
        ("consent_pending", "reject"): TransitionRule(target="cancelled", rule_id="CART_004_REJECT"),
        ("consent_pending", "timeout"): TransitionRule(target="expired", rule_id="CART_005_TIMEOUT"),
        ("authorized", "submit_payment"): TransitionRule(target="payment_pending", rule_id="CART_006_PAY"),
        ("payment_pending", "payment_confirmed"): TransitionRule(target="paid", rule_id="CART_007_PAID"),
        ("payment_pending", "payment_failed"): TransitionRule(target="authorized", rule_id="CART_008_PAY_FAIL"),
        ("payment_pending", "timeout"): TransitionRule(target="expired", rule_id="CART_009_TIMEOUT"),
        # Cancellation from any non-terminal state
        ("open", "cancel"): TransitionRule(target="cancelled", rule_id="CART_010_CANCEL"),
        ("priced", "cancel"): TransitionRule(target="cancelled", rule_id="CART_011_CANCEL"),
        ("authorized", "cancel"): TransitionRule(target="cancelled", rule_id="CART_012_CANCEL"),
    },
    terminal_states=frozenset({"paid", "expired", "cancelled"}),
)


# ═══════════════════════════════════════════════════════
# Order State Machine
# ═══════════════════════════════════════════════════════

ORDER_SM = StateMachine(
    name="order",
    transitions={
        ("created", "payment_initiated"): TransitionRule(target="payment_pending", rule_id="ORD_001_PAY_INIT"),
        ("payment_pending", "payment_confirmed"): TransitionRule(target="paid", rule_id="ORD_002_PAY_OK"),
        ("payment_pending", "payment_failed"): TransitionRule(target="payment_failed", rule_id="ORD_003_PAY_FAIL"),
        ("paid", "start_fulfillment"): TransitionRule(target="fulfilling", rule_id="ORD_004_FULFILL"),
        ("fulfilling", "ship"): TransitionRule(target="shipped", rule_id="ORD_005_SHIP"),
        ("shipped", "deliver"): TransitionRule(target="delivered", rule_id="ORD_006_DELIVER"),
        # Cancellation
        ("created", "cancel"): TransitionRule(target="cancelled", rule_id="ORD_007_CANCEL"),
        ("payment_pending", "cancel"): TransitionRule(target="cancelled", rule_id="ORD_008_CANCEL"),
        ("payment_failed", "retry_payment"): TransitionRule(target="payment_pending", rule_id="ORD_009_RETRY"),
        # Refund
        ("paid", "refund"): TransitionRule(target="refunded", rule_id="ORD_010_REFUND"),
        ("delivered", "refund"): TransitionRule(target="refunded", rule_id="ORD_011_REFUND"),
    },
    terminal_states=frozenset({"cancelled", "refunded"}),
)


# ═══════════════════════════════════════════════════════
# Payment State Machine (Local State)
#
# This tracks what WE did. The authoritative payment status
# comes from provider_confirmed_state via webhook.
# ═══════════════════════════════════════════════════════

PAYMENT_LOCAL_SM = StateMachine(
    name="payment_local",
    transitions={
        ("initiated", "send_to_provider"): TransitionRule(target="provider_requested", rule_id="PAY_001_REQUEST"),
        ("provider_requested", "provider_ack"): TransitionRule(target="provider_acknowledged", rule_id="PAY_002_ACK"),
        ("provider_requested", "provider_error"): TransitionRule(target="provider_error", rule_id="PAY_003_ERROR"),
        ("provider_error", "retry"): TransitionRule(target="provider_requested", rule_id="PAY_004_RETRY"),
        ("provider_error", "abandon"): TransitionRule(target="abandoned", rule_id="PAY_005_ABANDON"),
        ("provider_acknowledged", "webhook_success"): TransitionRule(target="completed", rule_id="PAY_006_COMPLETE"),
        ("provider_acknowledged", "webhook_failure"): TransitionRule(target="failed", rule_id="PAY_007_FAIL"),
        ("provider_acknowledged", "timeout"): TransitionRule(target="timeout", rule_id="PAY_008_TIMEOUT"),
        # Reconciliation can resolve ambiguous states
        ("timeout", "reconcile_success"): TransitionRule(target="completed", rule_id="PAY_009_RECONCILE_OK"),
        ("timeout", "reconcile_failure"): TransitionRule(target="failed", rule_id="PAY_010_RECONCILE_FAIL"),
    },
    terminal_states=frozenset({"completed", "failed", "abandoned"}),
)


# Provider confirmed states (set ONLY by verified webhook)
PROVIDER_CONFIRMED_STATES = frozenset({
    "captured",     # Payment captured successfully
    "failed",       # Payment failed at provider
    "refunded",     # Payment refunded
    "disputed",     # Chargeback/dispute
})
