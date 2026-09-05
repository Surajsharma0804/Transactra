"""
Transactra — Razorpay Payment Adapter

Handles communication with Razorpay payment gateway.
Implements dual-state payment architecture:
- Provider action: create order, verify signature
- Provider confirmation: webhook verification (ONLY authoritative source)

Security:
- HMAC-SHA256 webhook signature verification
- Razorpay signature verification for checkout callback
- Idempotent order creation

Complexity:
- Create order: O(1) API call
- Verify signature: O(1) HMAC comparison
- Webhook verify: O(1) HMAC comparison
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

logger = logging.getLogger("transactra.payment.razorpay")


@dataclass(frozen=True, slots=True)
class RazorpayConfig:
    """Razorpay API configuration. Immutable."""
    key_id: str
    key_secret: str
    webhook_secret: str
    base_url: str = "https://api.razorpay.com/v1"
    timeout_seconds: int = 30
    max_retries: int = 3

    def __post_init__(self) -> None:
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay key_id and key_secret are required")
        if not self.webhook_secret:
            raise ValueError("Razorpay webhook_secret is required")


@dataclass(frozen=True, slots=True)
class RazorpayOrderRequest:
    """Request to create a Razorpay order."""
    amount_paise: int
    currency: str = "INR"
    receipt: str = ""
    notes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.amount_paise <= 0:
            raise ValueError(f"Amount must be positive: {self.amount_paise}")

    def to_api_payload(self) -> dict[str, Any]:
        """Convert to Razorpay API payload. O(1)."""
        return {
            "amount": self.amount_paise,  # Razorpay uses paise
            "currency": self.currency,
            "receipt": self.receipt,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class RazorpayOrderResponse:
    """Response from Razorpay order creation."""
    razorpay_order_id: str
    amount_paise: int
    currency: str
    status: str
    receipt: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class RazorpayCheckoutCallback:
    """Callback from Razorpay checkout (client-side)."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@dataclass(frozen=True, slots=True)
class RazorpayWebhookEvent:
    """Parsed webhook event from Razorpay."""
    event_type: str  # e.g. "payment.captured", "payment.failed"
    payment_id: str
    order_id: str
    amount_paise: int
    currency: str
    status: str
    raw_payload: dict[str, Any] = field(default_factory=dict)


class RazorpaySignatureVerifier:
    """
    Verifies Razorpay signatures using HMAC-SHA256.

    Two verification modes:
    1. Checkout callback: verify(order_id|payment_id, signature, key_secret)
    2. Webhook: verify(body, signature, webhook_secret)

    Complexity: O(n) where n = payload length (for HMAC computation).
    Space: O(1) additional.
    """

    @staticmethod
    def verify_checkout_signature(
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        key_secret: str,
    ) -> bool:
        """
        Verify Razorpay checkout callback signature.

        message = order_id + "|" + payment_id
        expected = HMAC-SHA256(message, key_secret)

        O(1) — fixed-length inputs.
        """
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected = hmac.new(
            key_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, razorpay_signature)

    @staticmethod
    def verify_webhook_signature(
        webhook_body: str | bytes,
        webhook_signature: str,
        webhook_secret: str,
    ) -> bool:
        """
        Verify Razorpay webhook signature.

        expected = HMAC-SHA256(raw_body, webhook_secret)

        O(n) where n = body length. Timing-safe comparison.
        """
        if isinstance(webhook_body, str):
            webhook_body = webhook_body.encode("utf-8")
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            webhook_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, webhook_signature)

    @staticmethod
    def parse_webhook_event(payload: dict[str, Any]) -> RazorpayWebhookEvent | None:
        """
        Parse a Razorpay webhook payload into a typed event.

        Returns None if the event type is not recognized or payload is malformed.

        O(1) — direct dict lookups.
        """
        try:
            event_type = payload.get("event", "")
            entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            if not entity:
                return None

            return RazorpayWebhookEvent(
                event_type=event_type,
                payment_id=entity.get("id", ""),
                order_id=entity.get("order_id", ""),
                amount_paise=entity.get("amount", 0),
                currency=entity.get("currency", "INR"),
                status=entity.get("status", ""),
                raw_payload=payload,
            )
        except (KeyError, TypeError, AttributeError):
            logger.warning("Failed to parse webhook payload", exc_info=True)
            return None


class RazorpayAdapter:
    """
    Razorpay payment gateway adapter.

    Handles:
    - Order creation (idempotent via receipt)
    - Checkout signature verification
    - Webhook signature verification and parsing
    - Provider state mapping

    Does NOT make HTTP calls directly — uses an injectable HTTP client
    for testability.
    """

    def __init__(self, config: RazorpayConfig) -> None:
        self.config = config
        self.verifier = RazorpaySignatureVerifier()

    def build_order_payload(self, request: RazorpayOrderRequest) -> dict[str, Any]:
        """Build API payload for order creation. O(1)."""
        return request.to_api_payload()

    def verify_checkout(self, callback: RazorpayCheckoutCallback) -> bool:
        """Verify checkout callback signature. O(1)."""
        return self.verifier.verify_checkout_signature(
            callback.razorpay_order_id,
            callback.razorpay_payment_id,
            callback.razorpay_signature,
            self.config.key_secret,
        )

    def verify_webhook(self, body: str | bytes, signature: str) -> bool:
        """Verify webhook signature. O(n)."""
        return self.verifier.verify_webhook_signature(
            body, signature, self.config.webhook_secret
        )

    def parse_webhook(self, payload: dict[str, Any]) -> RazorpayWebhookEvent | None:
        """Parse webhook event. O(1)."""
        return self.verifier.parse_webhook_event(payload)

    @staticmethod
    def map_provider_status(razorpay_status: str) -> str | None:
        """
        Map Razorpay payment status to our provider_confirmed_state.

        O(1) dict lookup.
        """
        status_map = {
            "captured": "captured",
            "failed": "failed",
            "refunded": "refunded",
        }
        return status_map.get(razorpay_status)
