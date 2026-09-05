"""
Transactra — Mandate, Consent, Cart Unit Tests

Validates:
- Mandate: budget check, category/merchant filtering, type-specific rules
- Consent: cart hash binding (INV-06), expiry, single-use
- Cart: total formula, item validation, immutability
- CartItem: line total computation

All O(1) — no DB, no network.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.kernel.domain.mandate import (
    Cart,
    CartItem,
    CartStatus,
    Consent,
    ConsentStatus,
    Mandate,
    MandateStatus,
    MandateType,
)


# ═══════════════════════════════════════════════════════
# Mandate
# ═══════════════════════════════════════════════════════

class TestMandate:

    def test_active_mandate(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.PER_TRANSACTION,
            max_amount_paise=10_000_000,
        )
        assert m.is_active()

    def test_expired_by_time(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.DAILY,
            max_amount_paise=10_000_000,
            valid_until=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert not m.is_active()

    def test_not_yet_valid(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.DAILY,
            max_amount_paise=10_000_000,
            valid_from=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert not m.is_active()

    def test_revoked(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.DAILY,
            max_amount_paise=10_000_000,
            status=MandateStatus.REVOKED,
        )
        assert not m.is_active()

    def test_exhausted(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.DAILY,
            max_amount_paise=10_000_000,
            status=MandateStatus.EXHAUSTED,
        )
        assert not m.is_active()


class TestMandateBudget:

    def test_has_budget(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.PER_TRANSACTION,
            max_amount_paise=10_000_000,
            used_amount_paise=3_000_000,
        )
        assert m.has_budget_for(5_000_000)  # 7M remaining
        assert m.has_budget_for(7_000_000)  # exactly remaining
        assert not m.has_budget_for(7_000_001)  # 1 paise over

    def test_remaining(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.MONTHLY,
            max_amount_paise=10_000_000,
            used_amount_paise=4_000_000,
        )
        assert m.remaining_paise() == 6_000_000

    def test_fully_used(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.DAILY,
            max_amount_paise=10_000_000,
            used_amount_paise=10_000_000,
        )
        assert m.remaining_paise() == 0
        assert not m.has_budget_for(1)

    def test_zero_max_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            Mandate(
                mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
                mandate_type=MandateType.DAILY,
                max_amount_paise=0,
            )

    def test_used_exceeds_max_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds"):
            Mandate(
                mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
                mandate_type=MandateType.DAILY,
                max_amount_paise=10_000_000,
                used_amount_paise=15_000_000,
            )


class TestMandateFiltering:

    def test_category_allowed(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.PER_TRANSACTION,
            max_amount_paise=10_000_000,
            allowed_categories=frozenset({"laptops", "tablets"}),
        )
        assert m.category_allowed("laptops")
        assert m.category_allowed("tablets")
        assert not m.category_allowed("smartphones")

    def test_no_category_restriction(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.DAILY,
            max_amount_paise=10_000_000,
            allowed_categories=None,
        )
        assert m.category_allowed("anything")

    def test_merchant_allowed(self) -> None:
        mid = uuid4()
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.PER_TRANSACTION,
            max_amount_paise=10_000_000,
            allowed_merchant_ids=frozenset({mid}),
        )
        assert m.merchant_allowed(mid)
        assert not m.merchant_allowed(uuid4())

    def test_no_merchant_restriction(self) -> None:
        m = Mandate(
            mandate_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            mandate_type=MandateType.DAILY,
            max_amount_paise=10_000_000,
        )
        assert m.merchant_allowed(uuid4())


# ═══════════════════════════════════════════════════════
# Consent
# ═══════════════════════════════════════════════════════

class TestConsent:

    def test_approved_consent_valid(self) -> None:
        c = Consent(
            consent_id=uuid4(), user_id=uuid4(), mandate_id=uuid4(),
            cart_hash="abc123", amount_paise=6_800_000,
            status=ConsentStatus.APPROVED,
        )
        assert c.is_valid()

    def test_pending_consent_not_valid(self) -> None:
        c = Consent(
            consent_id=uuid4(), user_id=uuid4(), mandate_id=uuid4(),
            cart_hash="abc123", amount_paise=6_800_000,
            status=ConsentStatus.PENDING,
        )
        assert not c.is_valid()

    def test_expired_consent(self) -> None:
        c = Consent(
            consent_id=uuid4(), user_id=uuid4(), mandate_id=uuid4(),
            cart_hash="abc123", amount_paise=6_800_000,
            status=ConsentStatus.APPROVED,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        assert not c.is_valid()

    def test_consumed_consent_not_valid(self) -> None:
        c = Consent(
            consent_id=uuid4(), user_id=uuid4(), mandate_id=uuid4(),
            cart_hash="abc123", amount_paise=6_800_000,
            status=ConsentStatus.CONSUMED,
            consumed_at=datetime.now(timezone.utc),
        )
        assert not c.is_valid()


class TestConsentCartBinding:
    """INV-06: Cart change invalidates consent."""

    def test_matches_cart(self) -> None:
        c = Consent(
            consent_id=uuid4(), user_id=uuid4(), mandate_id=uuid4(),
            cart_hash="abc123def456", amount_paise=6_800_000,
        )
        assert c.matches_cart("abc123def456")

    def test_no_match_different_hash(self) -> None:
        c = Consent(
            consent_id=uuid4(), user_id=uuid4(), mandate_id=uuid4(),
            cart_hash="abc123def456", amount_paise=6_800_000,
        )
        assert not c.matches_cart("xyz789")

    def test_zero_amount_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            Consent(
                consent_id=uuid4(), user_id=uuid4(), mandate_id=uuid4(),
                cart_hash="abc", amount_paise=0,
            )


# ═══════════════════════════════════════════════════════
# CartItem
# ═══════════════════════════════════════════════════════

class TestCartItem:

    def test_auto_compute_line_total(self) -> None:
        item = CartItem(
            product_id=uuid4(), merchant_id=uuid4(), sku="LAP-001",
            title="Laptop", quantity=2, unit_price_paise=6_800_000,
            discount_paise=200_000,
        )
        # (6800000 × 2) - 200000 = 13400000
        assert item.line_total_paise == 13_400_000

    def test_explicit_line_total_correct(self) -> None:
        item = CartItem(
            product_id=uuid4(), merchant_id=uuid4(), sku="LAP-001",
            title="Laptop", quantity=1, unit_price_paise=6_800_000,
            discount_paise=0, line_total_paise=6_800_000,
        )
        assert item.line_total_paise == 6_800_000

    def test_explicit_line_total_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="mismatch"):
            CartItem(
                product_id=uuid4(), merchant_id=uuid4(), sku="LAP-001",
                title="Laptop", quantity=1, unit_price_paise=6_800_000,
                discount_paise=0, line_total_paise=5_000_000,
            )

    def test_zero_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            CartItem(
                product_id=uuid4(), merchant_id=uuid4(), sku="LAP-001",
                title="Laptop", quantity=0, unit_price_paise=6_800_000,
            )

    def test_negative_discount_raises(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            CartItem(
                product_id=uuid4(), merchant_id=uuid4(), sku="LAP-001",
                title="Laptop", quantity=1, unit_price_paise=6_800_000,
                discount_paise=-100,
            )

    def test_frozen(self) -> None:
        item = CartItem(
            product_id=uuid4(), merchant_id=uuid4(), sku="LAP-001",
            title="Laptop", quantity=1, unit_price_paise=6_800_000,
        )
        with pytest.raises(AttributeError):
            item.quantity = 5  # type: ignore[misc]


# ═══════════════════════════════════════════════════════
# Cart
# ═══════════════════════════════════════════════════════

class TestCart:

    def test_valid_cart(self) -> None:
        cart = Cart(
            cart_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            merchant_id=uuid4(),
            items=(
                CartItem(product_id=uuid4(), merchant_id=uuid4(),
                         sku="LAP-001", title="Laptop", quantity=1,
                         unit_price_paise=6_800_000),
            ),
            subtotal_paise=6_800_000,
            shipping_paise=50_000,
            tax_paise=1_233_000,
            discount_paise=200_000,
            total_paise=6_800_000 + 50_000 + 1_233_000 - 200_000,
        )
        assert cart.total_paise == 7_883_000

    def test_total_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="mismatch"):
            Cart(
                cart_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
                merchant_id=uuid4(),
                items=(),
                subtotal_paise=6_800_000,
                shipping_paise=50_000,
                tax_paise=0,
                discount_paise=0,
                total_paise=9_999_999,  # Wrong!
            )

    def test_negative_total_raises(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            Cart(
                cart_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
                merchant_id=uuid4(),
                items=(),
                subtotal_paise=100,
                shipping_paise=0,
                tax_paise=0,
                discount_paise=200,
                total_paise=-100,
            )

    def test_frozen(self) -> None:
        cart = Cart(
            cart_id=uuid4(), user_id=uuid4(), agent_id=uuid4(),
            merchant_id=uuid4(),
            items=(), subtotal_paise=0, shipping_paise=0,
            tax_paise=0, discount_paise=0, total_paise=0,
        )
        with pytest.raises(AttributeError):
            cart.total_paise = 999  # type: ignore[misc]
