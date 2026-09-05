"""
Transactra — Canonical Money Type

All financial amounts are integers in paise (smallest currency unit).
No floating point is ever used for authoritative monetary state.

Complexity: All operations O(1).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP


@dataclass(frozen=True, slots=True)
class Money:
    """
    Immutable monetary value in smallest currency unit (paise for INR).

    Invariants:
    - amount_paise is always a non-negative integer
    - currency is always a 3-letter ISO code
    - No floating point ever touches authoritative money state

    All operations are O(1) time, O(1) space.
    """

    amount_paise: int
    currency: str = "INR"

    def __post_init__(self) -> None:
        if not isinstance(self.amount_paise, int):
            raise TypeError(
                f"amount_paise must be int, got {type(self.amount_paise).__name__}. "
                f"Floating point is forbidden for authoritative monetary state."
            )
        if self.amount_paise < 0:
            raise ValueError(
                f"Money cannot be negative: {self.amount_paise} paise"
            )
        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise ValueError(
                f"Currency must be a 3-letter ISO code, got: {self.currency!r}"
            )

    # ── Arithmetic ───────────────────────────────────

    def add(self, other: Money) -> Money:
        """Add two Money values. Same currency required. O(1)."""
        self._assert_same_currency(other)
        return Money(self.amount_paise + other.amount_paise, self.currency)

    def subtract(self, other: Money) -> Money:
        """Subtract other from self. Result must be non-negative. O(1)."""
        self._assert_same_currency(other)
        result = self.amount_paise - other.amount_paise
        if result < 0:
            raise ValueError(
                f"Subtraction would result in negative money: "
                f"{self.amount_paise} - {other.amount_paise} = {result} paise"
            )
        return Money(result, self.currency)

    def multiply(self, quantity: int) -> Money:
        """Multiply by integer quantity. O(1)."""
        if not isinstance(quantity, int):
            raise TypeError(f"Quantity must be int, got {type(quantity).__name__}")
        if quantity < 0:
            raise ValueError(f"Quantity cannot be negative: {quantity}")
        return Money(self.amount_paise * quantity, self.currency)

    def is_within(self, limit: Money) -> bool:
        """Check if this amount is within the given limit. O(1)."""
        self._assert_same_currency(limit)
        return self.amount_paise <= limit.amount_paise

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

    # ── Comparison ───────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount_paise == other.amount_paise and self.currency == other.currency

    def __lt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount_paise < other.amount_paise

    def __le__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount_paise <= other.amount_paise

    def __gt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount_paise > other.amount_paise

    def __ge__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.amount_paise >= other.amount_paise

    # ── Display ──────────────────────────────────────

    def __repr__(self) -> str:
        rupees = self.amount_paise // 100
        paise = self.amount_paise % 100
        return f"Money(₹{rupees}.{paise:02d} {self.currency})"

    def to_display(self) -> str:
        """Human-readable display string. NOT for hashing or computation."""
        rupees = self.amount_paise // 100
        paise = self.amount_paise % 100
        return f"₹{rupees:,}.{paise:02d}"

    # ── Tax and Discount Calculations ────────────────

    @staticmethod
    def compute_tax(base_paise: int, tax_rate_bps: int) -> int:
        """
        Compute tax amount in paise.

        Args:
            base_paise: Base amount in paise (integer)
            tax_rate_bps: Tax rate in basis points (1800 = 18.00%)

        Returns:
            Tax amount in paise, rounded HALF UP.

        Rule: ROUND_HALF_UP — gives nearest integer, rounds 0.5 up.
        This is the standard tax rounding convention.

        Complexity: O(1).
        """
        if base_paise < 0:
            raise ValueError("Base amount cannot be negative")
        if tax_rate_bps < 0:
            raise ValueError("Tax rate cannot be negative")
        if tax_rate_bps == 0:
            return 0

        tax = Decimal(base_paise) * Decimal(tax_rate_bps) / Decimal(10_000)
        return int(tax.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    @staticmethod
    def compute_discount(
        base_paise: int,
        discount_rate_bps: int,
        floor_paise: int = 0,
    ) -> int:
        """
        Compute discount amount in paise with floor enforcement.

        Args:
            base_paise: Base amount in paise (integer)
            discount_rate_bps: Discount rate in basis points (500 = 5.00%)
            floor_paise: Minimum price after discount (merchant floor)

        Returns:
            Discount amount in paise, rounded DOWN (truncated).

        Rule: ROUND_DOWN — never give more discount than intended.
        Constraint: (base - discount) >= floor_paise.

        Complexity: O(1).
        """
        if base_paise < 0:
            raise ValueError("Base amount cannot be negative")
        if discount_rate_bps < 0:
            raise ValueError("Discount rate cannot be negative")
        if floor_paise < 0:
            raise ValueError("Floor cannot be negative")
        if discount_rate_bps == 0:
            return 0

        discount = Decimal(base_paise) * Decimal(discount_rate_bps) / Decimal(10_000)
        discount_int = int(discount.quantize(Decimal("1"), rounding=ROUND_DOWN))

        # Enforce floor: discount cannot push price below floor
        max_discount = max(0, base_paise - floor_paise)
        return min(discount_int, max_discount)

    @staticmethod
    def compute_line_total(
        unit_price_paise: int,
        quantity: int,
        discount_paise: int = 0,
    ) -> int:
        """
        Compute line item total: (unit_price × quantity) − discount.

        All integers. No rounding needed.
        Constraint: result >= 0.

        Complexity: O(1).
        """
        if unit_price_paise <= 0:
            raise ValueError("Unit price must be positive")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if discount_paise < 0:
            raise ValueError("Discount cannot be negative")

        total = (unit_price_paise * quantity) - discount_paise
        if total < 0:
            raise ValueError(
                f"Line total cannot be negative: "
                f"({unit_price_paise} × {quantity}) - {discount_paise} = {total}"
            )
        return total

    @staticmethod
    def compute_cart_total(
        line_totals: list[int],
        shipping_paise: int = 0,
        tax_paise: int = 0,
        cart_discount_paise: int = 0,
    ) -> int:
        """
        Compute cart total: sum(lines) + shipping + tax − discount.

        Integer arithmetic throughout.
        Constraint: result >= 0.

        Complexity: O(n) where n = number of line items.
        """
        if shipping_paise < 0:
            raise ValueError("Shipping cannot be negative")
        if tax_paise < 0:
            raise ValueError("Tax cannot be negative")
        if cart_discount_paise < 0:
            raise ValueError("Cart discount cannot be negative")

        subtotal = sum(line_totals)
        total = subtotal + shipping_paise + tax_paise - cart_discount_paise
        if total < 0:
            raise ValueError(
                f"Cart total cannot be negative: "
                f"{subtotal} + {shipping_paise} + {tax_paise} - {cart_discount_paise} = {total}"
            )
        return total
