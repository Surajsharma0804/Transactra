"""
Transactra — Order and Payment Domain Types

Order and Payment lifecycle types. Payment uses dual-state
architecture: local_state vs provider_confirmed_state.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


class OrderStatus(str, enum.Enum):
    CREATED = "created"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_FAILED = "payment_failed"
    PAID = "paid"
    FULFILLING = "fulfilling"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentLocalState(str, enum.Enum):
    """What we did — not authoritative."""
    INITIATED = "initiated"
    PROVIDER_REQUESTED = "provider_requested"
    PROVIDER_ACKNOWLEDGED = "provider_acknowledged"
    PROVIDER_ERROR = "provider_error"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ABANDONED = "abandoned"


class PaymentProviderState(str, enum.Enum):
    """What the provider confirmed — AUTHORITATIVE."""
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


@dataclass(frozen=True, slots=True)
class Order:
    """
    Order record. Created after successful authorization.

    State machine: ORDER_SM (see commerce_states.py).
    """
    order_id: UUID
    user_id: UUID
    cart_id: UUID
    mandate_id: UUID
    consent_id: UUID
    authorization_decision_id: UUID
    merchant_id: UUID
    total_paise: int
    currency: str = "INR"
    status: OrderStatus = OrderStatus.CREATED
    idempotency_key: str = ""
    authorization_nonce: str = ""
    cart_hash: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class Payment:
    """
    Payment record with dual-state architecture.

    - local_state: What we did (initiated, requested, etc.)
    - provider_confirmed_state: What the webhook confirmed (captured, failed, etc.)

    Only provider_confirmed_state is authoritative for "is this paid?"
    This separation prevents:
    - Client-side payment forgery
    - Race conditions between client callback and webhook
    - False positives from network timeouts

    INV-09: Only verified provider webhook can set provider_confirmed_state.
    """
    payment_id: UUID
    order_id: UUID
    amount_paise: int
    currency: str = "INR"
    local_state: PaymentLocalState = PaymentLocalState.INITIATED
    provider_confirmed_state: PaymentProviderState | None = None
    # Razorpay-specific fields
    provider_order_id: str | None = None   # razorpay_order_id
    provider_payment_id: str | None = None  # razorpay_payment_id
    provider_signature: str | None = None   # razorpay_signature
    # Idempotency (separate from authorization nonce)
    idempotency_key: str = ""
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    provider_confirmed_at: datetime | None = None

    def is_paid(self) -> bool:
        """
        ONLY true if the PROVIDER confirmed capture.
        Local state alone is NOT sufficient.
        O(1).
        """
        return self.provider_confirmed_state == PaymentProviderState.CAPTURED

    def is_failed(self) -> bool:
        """Provider confirmed failure. O(1)."""
        return self.provider_confirmed_state == PaymentProviderState.FAILED

    def needs_reconciliation(self) -> bool:
        """
        Ambiguous state: we sent to provider but haven't heard back.
        O(1).
        """
        return (
            self.local_state in (
                PaymentLocalState.PROVIDER_REQUESTED,
                PaymentLocalState.PROVIDER_ACKNOWLEDGED,
                PaymentLocalState.TIMEOUT,
            )
            and self.provider_confirmed_state is None
        )

    def __post_init__(self) -> None:
        if self.amount_paise <= 0:
            raise ValueError(f"Payment amount must be positive: {self.amount_paise}")
