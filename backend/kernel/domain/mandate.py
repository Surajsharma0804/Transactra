"""
Transactra — Mandate Domain Types

A mandate is a user-defined spending authority: "My agent can spend up
to ₹X on category Y within time window Z."

Mandates are the formal delegation of limited authority from a user
to their agent. They are:
- Bound to a principal (user)
- Type-specific (per_transaction, daily, weekly, monthly, one_time)
- Cart-bound when activated (exact hash match required)
- Consumed or expired, never reused
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


class MandateType(str, enum.Enum):
    """Type of spending mandate."""
    PER_TRANSACTION = "per_transaction"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ONE_TIME = "one_time"


class MandateStatus(str, enum.Enum):
    """Mandate lifecycle status."""
    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class Mandate:
    """
    Spending authority delegation.

    Invariants:
    - max_amount_paise > 0 (positive spending limit)
    - used_amount_paise <= max_amount_paise
    - Child authority ⊆ Parent authority (delegation never escalates)
    - ONE_TIME: cart_hash/bound_amount_paise required when bound
    - DAILY/WEEKLY/MONTHLY: no cart binding, rolling window

    Complexity:
    - is_active: O(1)
    - has_budget_for: O(1)
    - category_allowed: O(k) where k = allowed categories
    """
    mandate_id: UUID
    user_id: UUID
    agent_id: UUID
    mandate_type: MandateType
    max_amount_paise: int
    used_amount_paise: int = 0
    currency: str = "INR"
    allowed_categories: frozenset[str] | None = None
    allowed_merchant_ids: frozenset[UUID] | None = None
    status: MandateStatus = MandateStatus.ACTIVE
    # Cart binding (set on authorization, not creation)
    cart_hash: str | None = None
    bound_amount_paise: int | None = None
    # Time window
    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_active(self, now: datetime | None = None) -> bool:
        """Check if mandate is active and not expired. O(1)."""
        if self.status != MandateStatus.ACTIVE:
            return False
        current = now or datetime.now(timezone.utc)
        if current < self.valid_from:
            return False
        if self.valid_until is not None and current > self.valid_until:
            return False
        return True

    def has_budget_for(self, amount_paise: int) -> bool:
        """Check if mandate has budget for the given amount. O(1)."""
        remaining = self.max_amount_paise - self.used_amount_paise
        return amount_paise <= remaining

    def remaining_paise(self) -> int:
        """Remaining budget in paise. O(1)."""
        return max(0, self.max_amount_paise - self.used_amount_paise)

    def category_allowed(self, category: str) -> bool:
        """Check if category is in allowed set. O(k) where k = allowed categories."""
        if self.allowed_categories is None:
            return True  # No restriction
        return category in self.allowed_categories

    def merchant_allowed(self, merchant_id: UUID) -> bool:
        """Check if merchant is in allowed set. O(k) where k = allowed merchants."""
        if self.allowed_merchant_ids is None:
            return True  # No restriction
        return merchant_id in self.allowed_merchant_ids

    def __post_init__(self) -> None:
        if self.max_amount_paise <= 0:
            raise ValueError(f"max_amount_paise must be positive: {self.max_amount_paise}")
        if self.used_amount_paise < 0:
            raise ValueError(f"used_amount_paise cannot be negative: {self.used_amount_paise}")
        if self.used_amount_paise > self.max_amount_paise:
            raise ValueError(
                f"used ({self.used_amount_paise}) exceeds max ({self.max_amount_paise})"
            )


class ConsentStatus(str, enum.Enum):
    """Consent lifecycle status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONSUMED = "consumed"


@dataclass(frozen=True, slots=True)
class Consent:
    """
    User approval of a specific transaction.

    Consent binds to an EXACT cart hash. If the cart changes after consent,
    the hash won't match → authorization denied.

    Consent is single-use: once consumed by a successful authorization,
    it cannot be reused.

    Invariants:
    - INV-06: Cart change invalidates consent (cart_hash mismatch)
    - Consent is bound to a specific mandate
    - Consent is consumed atomically with authorization
    """
    consent_id: UUID
    user_id: UUID
    mandate_id: UUID
    cart_hash: str
    amount_paise: int
    currency: str = "INR"
    status: ConsentStatus = ConsentStatus.PENDING
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    consumed_at: datetime | None = None

    def is_valid(self, now: datetime | None = None) -> bool:
        """Check if consent is approved and not expired. O(1)."""
        if self.status != ConsentStatus.APPROVED:
            return False
        if self.expires_at is not None:
            current = now or datetime.now(timezone.utc)
            if current > self.expires_at:
                return False
        return True

    def matches_cart(self, cart_hash: str) -> bool:
        """INV-06: Verify exact cart binding. O(1) string compare."""
        return self.cart_hash == cart_hash

    def __post_init__(self) -> None:
        if self.amount_paise <= 0:
            raise ValueError(f"Consent amount must be positive: {self.amount_paise}")


@dataclass(frozen=True, slots=True)
class CartItem:
    """Single item in a cart. Immutable after creation."""
    product_id: UUID
    merchant_id: UUID
    sku: str
    title: str
    quantity: int
    unit_price_paise: int
    discount_paise: int = 0
    line_total_paise: int = 0

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive: {self.quantity}")
        if self.unit_price_paise <= 0:
            raise ValueError(f"Unit price must be positive: {self.unit_price_paise}")
        if self.discount_paise < 0:
            raise ValueError(f"Discount cannot be negative: {self.discount_paise}")
        # Compute line total if not provided
        expected = (self.unit_price_paise * self.quantity) - self.discount_paise
        if self.line_total_paise == 0:
            object.__setattr__(self, "line_total_paise", expected)
        elif self.line_total_paise != expected:
            raise ValueError(
                f"Line total mismatch: {self.line_total_paise} != "
                f"({self.unit_price_paise} × {self.quantity}) - {self.discount_paise} = {expected}"
            )


class CartStatus(str, enum.Enum):
    """Cart lifecycle states."""
    OPEN = "open"
    PRICED = "priced"
    CONSENT_PENDING = "consent_pending"
    AUTHORIZED = "authorized"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class Cart:
    """
    Shopping cart with exact pricing and hash binding.

    Cart total = sum(line_totals) + shipping_paise + tax_paise - discount_paise.
    All arithmetic integer. Hash computed via canonical serialization.

    Invariants:
    - total_paise must equal computed total from components
    - cart_hash changes on any modification (INV-06)
    - Once consent-bound, cart is immutable
    """
    cart_id: UUID
    user_id: UUID
    agent_id: UUID
    merchant_id: UUID
    items: tuple[CartItem, ...]
    subtotal_paise: int
    shipping_paise: int
    tax_paise: int
    discount_paise: int
    total_paise: int
    currency: str = "INR"
    cart_hash: str = ""
    status: CartStatus = CartStatus.OPEN
    warranty_months: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        # Validate total
        expected = self.subtotal_paise + self.shipping_paise + self.tax_paise - self.discount_paise
        if self.total_paise != expected:
            raise ValueError(
                f"Cart total mismatch: {self.total_paise} != "
                f"{self.subtotal_paise} + {self.shipping_paise} + {self.tax_paise} - {self.discount_paise} = {expected}"
            )
        if self.total_paise < 0:
            raise ValueError(f"Cart total cannot be negative: {self.total_paise}")
