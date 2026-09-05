"""
Transactra — Money Type Unit Tests

Validates:
- INV-01: Financial amounts are integers in paise — no floating point
- All arithmetic is integer-based
- Tax rounding: HALF_UP
- Discount rounding: DOWN (truncate), with floor enforcement
- Line totals and cart totals are correct
- Edge cases: zero, overflow, currency mismatch

Every test is O(1) — no DB, no network.
"""

from __future__ import annotations

import pytest

from backend.kernel.domain.money import Money


# ═══════════════════════════════════════════════════════
# INV-01: Integer enforcement — no float allowed
# ═══════════════════════════════════════════════════════

class TestMoneyIntegerEnforcement:
    """Money must ONLY accept integers. Float is forbidden."""

    def test_float_amount_raises_type_error(self) -> None:
        """Floating point amounts must be rejected at construction."""
        with pytest.raises(TypeError, match="amount_paise must be int"):
            Money(amount_paise=1.5)  # type: ignore[arg-type]

    def test_float_zero_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="amount_paise must be int"):
            Money(amount_paise=0.0)  # type: ignore[arg-type]

    def test_string_amount_raises_type_error(self) -> None:
        with pytest.raises(TypeError, match="amount_paise must be int"):
            Money(amount_paise="100")  # type: ignore[arg-type]

    def test_bool_amount_accepted_as_int(self) -> None:
        """bool is subclass of int in Python — this is valid (True=1, False=0)."""
        m = Money(amount_paise=True)
        assert m.amount_paise == 1

    def test_negative_amount_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            Money(amount_paise=-1)

    def test_zero_amount_valid(self) -> None:
        m = Money(amount_paise=0)
        assert m.amount_paise == 0

    def test_large_amount_valid(self) -> None:
        """Supports amounts up to ₹99,99,999 (10M paise)."""
        m = Money(amount_paise=999_999_900)
        assert m.amount_paise == 999_999_900

    def test_currency_must_be_three_chars(self) -> None:
        with pytest.raises(ValueError, match="3-letter ISO code"):
            Money(amount_paise=100, currency="IN")

    def test_currency_default_is_inr(self) -> None:
        m = Money(amount_paise=100)
        assert m.currency == "INR"


# ═══════════════════════════════════════════════════════
# Arithmetic
# ═══════════════════════════════════════════════════════

class TestMoneyArithmetic:
    """All arithmetic is integer-based. No rounding needed."""

    def test_add(self) -> None:
        a = Money(7000000)
        b = Money(500000)
        result = a.add(b)
        assert result.amount_paise == 7500000
        assert isinstance(result.amount_paise, int)

    def test_subtract(self) -> None:
        a = Money(7000000)
        b = Money(500000)
        result = a.subtract(b)
        assert result.amount_paise == 6500000

    def test_subtract_to_zero(self) -> None:
        a = Money(100)
        b = Money(100)
        result = a.subtract(b)
        assert result.amount_paise == 0

    def test_subtract_negative_raises(self) -> None:
        a = Money(100)
        b = Money(200)
        with pytest.raises(ValueError, match="negative money"):
            a.subtract(b)

    def test_multiply(self) -> None:
        unit = Money(6800000)  # ₹68,000
        result = unit.multiply(2)
        assert result.amount_paise == 13600000

    def test_multiply_by_zero(self) -> None:
        result = Money(6800000).multiply(0)
        assert result.amount_paise == 0

    def test_multiply_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            Money(100).multiply(-1)

    def test_multiply_float_raises(self) -> None:
        with pytest.raises(TypeError, match="int"):
            Money(100).multiply(1.5)  # type: ignore[arg-type]

    def test_currency_mismatch_add(self) -> None:
        a = Money(100, "INR")
        b = Money(100, "USD")
        with pytest.raises(ValueError, match="Currency mismatch"):
            a.add(b)

    def test_currency_mismatch_subtract(self) -> None:
        a = Money(100, "INR")
        b = Money(50, "USD")
        with pytest.raises(ValueError, match="Currency mismatch"):
            a.subtract(b)


# ═══════════════════════════════════════════════════════
# Comparison
# ═══════════════════════════════════════════════════════

class TestMoneyComparison:

    def test_equal(self) -> None:
        assert Money(100) == Money(100)

    def test_not_equal_amount(self) -> None:
        assert Money(100) != Money(200)

    def test_not_equal_currency(self) -> None:
        assert Money(100, "INR") != Money(100, "USD")

    def test_less_than(self) -> None:
        assert Money(100) < Money(200)

    def test_less_equal(self) -> None:
        assert Money(100) <= Money(100)

    def test_greater_than(self) -> None:
        assert Money(200) > Money(100)

    def test_is_within(self) -> None:
        amount = Money(6800000)  # ₹68,000
        limit = Money(7000000)   # ₹70,000
        assert amount.is_within(limit)

    def test_is_not_within(self) -> None:
        amount = Money(8500000)  # ₹85,000
        limit = Money(7000000)   # ₹70,000
        assert not amount.is_within(limit)


# ═══════════════════════════════════════════════════════
# Immutability
# ═══════════════════════════════════════════════════════

class TestMoneyImmutability:
    """Money is frozen — no mutation after creation."""

    def test_frozen(self) -> None:
        m = Money(100)
        with pytest.raises(AttributeError):
            m.amount_paise = 200  # type: ignore[misc]

    def test_add_returns_new_instance(self) -> None:
        a = Money(100)
        b = Money(200)
        c = a.add(b)
        assert a.amount_paise == 100  # unchanged
        assert c.amount_paise == 300


# ═══════════════════════════════════════════════════════
# Tax Calculation — ROUND HALF UP
# ═══════════════════════════════════════════════════════

class TestTaxComputation:
    """Tax uses ROUND_HALF_UP — standard tax rounding."""

    def test_18_percent_gst(self) -> None:
        """₹1,000 × 18% = ₹180.00 = 18000 paise."""
        tax = Money.compute_tax(base_paise=100_000, tax_rate_bps=1800)
        assert tax == 18_000
        assert isinstance(tax, int)

    def test_18_percent_on_odd_base(self) -> None:
        """₹999.99 (99999 paise) × 18% = 17999.82 → 17999.82 rounds to 18000."""
        tax = Money.compute_tax(base_paise=99_999, tax_rate_bps=1800)
        assert tax == 18_000  # 99999 * 1800 / 10000 = 17999.82 → rounds to 18000

    def test_half_rounds_up(self) -> None:
        """5 × 1000 bps / 10000 = 0.5 → rounds UP to 1."""
        tax = Money.compute_tax(base_paise=5, tax_rate_bps=1000)
        assert tax == 1  # 0.5 rounds up

    def test_zero_rate(self) -> None:
        tax = Money.compute_tax(base_paise=100_000, tax_rate_bps=0)
        assert tax == 0

    def test_zero_base(self) -> None:
        tax = Money.compute_tax(base_paise=0, tax_rate_bps=1800)
        assert tax == 0

    def test_negative_base_raises(self) -> None:
        with pytest.raises(ValueError):
            Money.compute_tax(base_paise=-100, tax_rate_bps=1800)

    def test_negative_rate_raises(self) -> None:
        with pytest.raises(ValueError):
            Money.compute_tax(base_paise=100, tax_rate_bps=-100)

    def test_result_is_always_integer(self) -> None:
        """Tax on various bases must always produce an integer."""
        for base in [1, 7, 13, 99, 101, 333, 99999, 6_800_000]:
            tax = Money.compute_tax(base_paise=base, tax_rate_bps=1800)
            assert isinstance(tax, int), f"Failed for base={base}"


# ═══════════════════════════════════════════════════════
# Discount Calculation — ROUND DOWN + Floor
# ═══════════════════════════════════════════════════════

class TestDiscountComputation:
    """Discount uses ROUND_DOWN — never give more than intended."""

    def test_5_percent_discount(self) -> None:
        """₹68,000 × 5% = ₹3,400 = 340000 paise."""
        disc = Money.compute_discount(base_paise=6_800_000, discount_rate_bps=500)
        assert disc == 340_000

    def test_rounds_down(self) -> None:
        """7 × 333 bps / 10000 = 0.2331 → truncates to 0."""
        disc = Money.compute_discount(base_paise=7, discount_rate_bps=333)
        assert disc == 0  # 0.2331 rounds down

    def test_floor_enforcement(self) -> None:
        """Discount cannot push price below floor."""
        # ₹68,000 × 10% = ₹6,800, but floor is ₹64,500
        # Max discount = 68000 - 64500 = 3500 = 350000 paise
        disc = Money.compute_discount(
            base_paise=6_800_000,
            discount_rate_bps=1000,   # 10% = 680000 paise
            floor_paise=6_450_000,     # ₹64,500
        )
        assert disc == 350_000  # capped at 350000

    def test_no_floor(self) -> None:
        """Without floor, full discount applies."""
        disc = Money.compute_discount(
            base_paise=6_800_000,
            discount_rate_bps=1000,   # 10% = 680000
        )
        assert disc == 680_000

    def test_zero_rate(self) -> None:
        disc = Money.compute_discount(base_paise=100_000, discount_rate_bps=0)
        assert disc == 0

    def test_result_is_always_integer(self) -> None:
        for base in [1, 7, 13, 99, 101, 6_800_000]:
            disc = Money.compute_discount(base_paise=base, discount_rate_bps=333)
            assert isinstance(disc, int), f"Failed for base={base}"


# ═══════════════════════════════════════════════════════
# Line Total
# ═══════════════════════════════════════════════════════

class TestLineTotalComputation:
    """Line total = (unit_price × quantity) − discount."""

    def test_simple_line(self) -> None:
        total = Money.compute_line_total(unit_price_paise=6_800_000, quantity=1)
        assert total == 6_800_000

    def test_with_quantity(self) -> None:
        total = Money.compute_line_total(unit_price_paise=50_000, quantity=3)
        assert total == 150_000

    def test_with_discount(self) -> None:
        total = Money.compute_line_total(
            unit_price_paise=6_800_000, quantity=1, discount_paise=200_000
        )
        assert total == 6_600_000

    def test_discount_exceeds_value_raises(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            Money.compute_line_total(
                unit_price_paise=100, quantity=1, discount_paise=200
            )

    def test_zero_unit_price_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            Money.compute_line_total(unit_price_paise=0, quantity=1)

    def test_zero_quantity_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            Money.compute_line_total(unit_price_paise=100, quantity=0)


# ═══════════════════════════════════════════════════════
# Cart Total
# ═══════════════════════════════════════════════════════

class TestCartTotalComputation:
    """Cart total = sum(lines) + shipping + tax − discount."""

    def test_simple_cart(self) -> None:
        total = Money.compute_cart_total(
            line_totals=[6_800_000],
            shipping_paise=50_000,
            tax_paise=1_224_000,  # 18% of 68000
        )
        assert total == 8_074_000

    def test_multi_item_cart(self) -> None:
        total = Money.compute_cart_total(
            line_totals=[6_800_000, 50_000, 30_000],
            shipping_paise=0,
            tax_paise=1_238_400,
        )
        assert total == 6_800_000 + 50_000 + 30_000 + 1_238_400

    def test_with_cart_discount(self) -> None:
        total = Money.compute_cart_total(
            line_totals=[6_800_000],
            shipping_paise=50_000,
            tax_paise=1_224_000,
            cart_discount_paise=200_000,
        )
        assert total == 6_800_000 + 50_000 + 1_224_000 - 200_000

    def test_empty_cart(self) -> None:
        total = Money.compute_cart_total(line_totals=[], shipping_paise=0, tax_paise=0)
        assert total == 0

    def test_negative_total_raises(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            Money.compute_cart_total(
                line_totals=[100],
                shipping_paise=0,
                tax_paise=0,
                cart_discount_paise=200,
            )


# ═══════════════════════════════════════════════════════
# Display
# ═══════════════════════════════════════════════════════

class TestMoneyDisplay:

    def test_repr(self) -> None:
        m = Money(6_800_000)
        r = repr(m)
        assert "68000" in r
        assert "INR" in r

    def test_display(self) -> None:
        m = Money(6_800_050)
        d = m.to_display()
        assert "68,000.50" in d

    def test_display_zero(self) -> None:
        m = Money(0)
        d = m.to_display()
        assert "0.00" in d
