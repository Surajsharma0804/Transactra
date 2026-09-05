"""
Transactra — Razorpay Adapter Tests

Validates:
- HMAC-SHA256 checkout signature verification
- HMAC-SHA256 webhook signature verification (timing-safe)
- Webhook event parsing
- Provider status mapping
- Configuration validation

All O(1) — no network calls.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from uuid import uuid4

import pytest

from adapters.payment.razorpay import (
    RazorpayAdapter,
    RazorpayCheckoutCallback,
    RazorpayConfig,
    RazorpayOrderRequest,
    RazorpaySignatureVerifier,
)


# ── Test Config ──────────────────────────────────────

TEST_KEY_ID = "rzp_test_abc123"
TEST_KEY_SECRET = "test_secret_key_1234567890"
TEST_WEBHOOK_SECRET = "whsec_test_webhook_secret_abcdef"


def _config() -> RazorpayConfig:
    return RazorpayConfig(
        key_id=TEST_KEY_ID,
        key_secret=TEST_KEY_SECRET,
        webhook_secret=TEST_WEBHOOK_SECRET,
    )


def _compute_checkout_sig(order_id: str, payment_id: str) -> str:
    """Compute valid Razorpay checkout signature for testing."""
    message = f"{order_id}|{payment_id}"
    return hmac.new(
        TEST_KEY_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _compute_webhook_sig(body: str) -> str:
    """Compute valid Razorpay webhook signature for testing."""
    return hmac.new(
        TEST_WEBHOOK_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


# ═══════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════

class TestConfig:

    def test_valid_config(self) -> None:
        config = _config()
        assert config.key_id == TEST_KEY_ID
        assert config.timeout_seconds == 30

    def test_empty_key_raises(self) -> None:
        with pytest.raises(ValueError, match="key_id"):
            RazorpayConfig(key_id="", key_secret="s", webhook_secret="w")

    def test_empty_webhook_secret_raises(self) -> None:
        with pytest.raises(ValueError, match="webhook_secret"):
            RazorpayConfig(key_id="k", key_secret="s", webhook_secret="")

    def test_config_frozen(self) -> None:
        config = _config()
        with pytest.raises(AttributeError):
            config.key_id = "new"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════
# Checkout Signature Verification
# ═══════════════════════════════════════════════════════

class TestCheckoutSignature:

    def test_valid_signature(self) -> None:
        order_id = "order_TestOrder123"
        payment_id = "pay_TestPay456"
        sig = _compute_checkout_sig(order_id, payment_id)

        adapter = RazorpayAdapter(_config())
        callback = RazorpayCheckoutCallback(
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            razorpay_signature=sig,
        )
        assert adapter.verify_checkout(callback)

    def test_invalid_signature(self) -> None:
        adapter = RazorpayAdapter(_config())
        callback = RazorpayCheckoutCallback(
            razorpay_order_id="order_123",
            razorpay_payment_id="pay_456",
            razorpay_signature="invalid_sig_abcdef",
        )
        assert not adapter.verify_checkout(callback)

    def test_tampered_order_id(self) -> None:
        order_id = "order_Original"
        payment_id = "pay_456"
        sig = _compute_checkout_sig(order_id, payment_id)

        adapter = RazorpayAdapter(_config())
        callback = RazorpayCheckoutCallback(
            razorpay_order_id="order_Tampered",  # Changed!
            razorpay_payment_id=payment_id,
            razorpay_signature=sig,
        )
        assert not adapter.verify_checkout(callback)

    def test_tampered_payment_id(self) -> None:
        order_id = "order_123"
        payment_id = "pay_Original"
        sig = _compute_checkout_sig(order_id, payment_id)

        adapter = RazorpayAdapter(_config())
        callback = RazorpayCheckoutCallback(
            razorpay_order_id=order_id,
            razorpay_payment_id="pay_Tampered",  # Changed!
            razorpay_signature=sig,
        )
        assert not adapter.verify_checkout(callback)


# ═══════════════════════════════════════════════════════
# Webhook Signature Verification
# ═══════════════════════════════════════════════════════

class TestWebhookSignature:

    def test_valid_webhook(self) -> None:
        body = json.dumps({"event": "payment.captured", "payload": {}})
        sig = _compute_webhook_sig(body)

        adapter = RazorpayAdapter(_config())
        assert adapter.verify_webhook(body, sig)

    def test_invalid_webhook(self) -> None:
        adapter = RazorpayAdapter(_config())
        assert not adapter.verify_webhook("some body", "invalid_sig")

    def test_tampered_body(self) -> None:
        original_body = json.dumps({"event": "payment.captured"})
        sig = _compute_webhook_sig(original_body)

        tampered_body = json.dumps({"event": "payment.captured", "tampered": True})
        adapter = RazorpayAdapter(_config())
        assert not adapter.verify_webhook(tampered_body, sig)

    def test_bytes_body(self) -> None:
        body = b'{"event": "payment.captured"}'
        sig = _compute_webhook_sig(body.decode("utf-8"))

        adapter = RazorpayAdapter(_config())
        assert adapter.verify_webhook(body, sig)


# ═══════════════════════════════════════════════════════
# Webhook Parsing
# ═══════════════════════════════════════════════════════

class TestWebhookParsing:

    def test_parse_payment_captured(self) -> None:
        payload = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_12345",
                        "order_id": "order_67890",
                        "amount": 6_800_000,
                        "currency": "INR",
                        "status": "captured",
                    }
                }
            },
        }
        adapter = RazorpayAdapter(_config())
        event = adapter.parse_webhook(payload)
        assert event is not None
        assert event.event_type == "payment.captured"
        assert event.payment_id == "pay_12345"
        assert event.order_id == "order_67890"
        assert event.amount_paise == 6_800_000
        assert event.status == "captured"

    def test_parse_payment_failed(self) -> None:
        payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_fail_1",
                        "order_id": "order_99",
                        "amount": 1_000_000,
                        "currency": "INR",
                        "status": "failed",
                    }
                }
            },
        }
        adapter = RazorpayAdapter(_config())
        event = adapter.parse_webhook(payload)
        assert event is not None
        assert event.status == "failed"

    def test_parse_malformed_payload(self) -> None:
        adapter = RazorpayAdapter(_config())
        assert adapter.parse_webhook({}) is None
        assert adapter.parse_webhook({"event": "unknown"}) is None


# ═══════════════════════════════════════════════════════
# Provider Status Mapping
# ═══════════════════════════════════════════════════════

class TestProviderMapping:

    def test_captured(self) -> None:
        assert RazorpayAdapter.map_provider_status("captured") == "captured"

    def test_failed(self) -> None:
        assert RazorpayAdapter.map_provider_status("failed") == "failed"

    def test_refunded(self) -> None:
        assert RazorpayAdapter.map_provider_status("refunded") == "refunded"

    def test_unknown_returns_none(self) -> None:
        assert RazorpayAdapter.map_provider_status("unknown_state") is None


# ═══════════════════════════════════════════════════════
# Order Request
# ═══════════════════════════════════════════════════════

class TestOrderRequest:

    def test_valid_request(self) -> None:
        req = RazorpayOrderRequest(
            amount_paise=6_800_000, currency="INR", receipt="ord_123"
        )
        payload = req.to_api_payload()
        assert payload["amount"] == 6_800_000
        assert payload["currency"] == "INR"

    def test_zero_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            RazorpayOrderRequest(amount_paise=0)
