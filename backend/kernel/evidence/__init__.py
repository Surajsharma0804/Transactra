"""
Transactra — Canonical JSON Serialization

Deterministic JSON serialization for hashing and proof verification.
Two implementations must produce the SAME hash for the SAME data.

Algorithm v1.0 — Rules:
  1.  ENCODING:     UTF-8, no BOM
  2.  KEYS:         Sorted alphabetically (Unicode code point order), recursive
  3.  SEPARATORS:   ',' between elements, ':' between key-value (no whitespace)
  4.  STRINGS:      Double-quoted, ASCII-escaped (ensure_ascii=True)
  5.  NULL:         JSON null (not omitted, not empty string)
  6.  BOOLEANS:     JSON true/false (lowercase)
  7.  INTEGERS:     JSON number, no decimal point, no leading zeros
  8.  FLOATS:       PROHIBITED — raises ValueError
  9.  UUIDS:        Lowercase string with hyphens
  10. TIMESTAMPS:   ISO 8601 UTC with 'Z' suffix, no offset
  11. ARRAYS:       Maintain original order (do NOT sort elements)
  12. NESTED:       Apply rules recursively
  13. HASH:         SHA-256 of UTF-8 bytes, lowercase hex (64 chars)

Complexity: O(n) where n = total size of serialized output.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID


SERIALIZATION_VERSION = "1.0"


def _canonical_serializer(obj: object) -> object:
    """
    Custom JSON serializer for canonical output.

    Handles: UUID, datetime, None.
    Rejects: float (explicitly forbidden for money).

    Complexity: O(1) per value.
    """
    if isinstance(obj, UUID):
        # Rule 9: lowercase with hyphens
        return str(obj).lower()

    if isinstance(obj, datetime):
        # Rule 10: ISO 8601 UTC with 'Z', no offset
        utc_dt = obj.astimezone(timezone.utc) if obj.tzinfo else obj
        # Include milliseconds only if non-zero
        if utc_dt.microsecond:
            return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc_dt.microsecond:06d}".rstrip("0") + "Z"
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    if isinstance(obj, float):
        # Rule 8: PROHIBITED
        raise ValueError(
            f"Float values are prohibited in canonical serialization: {obj}. "
            f"Use integer paise for monetary values."
        )

    # Let json.dumps handle the error for truly unsupported types
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def canonical_json(obj: dict) -> str:
    """
    Produce deterministic canonical JSON string.

    Guarantees that the same logical data always produces the same string,
    regardless of Python dict insertion order or platform.

    Complexity: O(n log n) due to key sorting, where n = number of keys (all levels).
    Space: O(n) for output string.
    """
    return json.dumps(
        obj,
        sort_keys=True,           # Rule 2
        separators=(",", ":"),    # Rule 3
        default=_canonical_serializer,
        ensure_ascii=True,        # Rule 4
    )


def canonical_hash(obj: dict) -> str:
    """
    SHA-256 hash of canonical JSON representation.

    Returns: lowercase hex string (64 characters).

    Complexity: O(n) serialization + O(n) hashing.
    Space: O(n) for serialized string + O(1) for hash.
    """
    canonical = canonical_json(obj)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_cart_hash(
    merchant_id: UUID,
    items: list[dict],
    subtotal_paise: int,
    shipping_paise: int,
    tax_paise: int,
    discount_paise: int,
    total_paise: int,
    currency: str = "INR",
    warranty_months: int = 0,
) -> str:
    """
    Compute the canonical hash of a cart for exact-cart binding.

    Any change to cart contents, prices, quantities, shipping, tax,
    discount, or merchant produces a different hash.

    This hash is stored in the mandate, consent, and authorization.
    If the cart changes after consent, the hash won't match → DENY.

    Complexity: O(n) where n = number of line items.
    """
    canonical_items = [
        {
            "discount_paise": item["discount_paise"],
            "line_total_paise": item["line_total_paise"],
            "product_id": str(item["product_id"]).lower() if isinstance(item["product_id"], UUID) else str(item["product_id"]).lower(),
            "quantity": item["quantity"],
            "sku": item["sku"],
            "unit_price_paise": item["unit_price_paise"],
        }
        for item in sorted(items, key=lambda x: x["sku"])
    ]

    return canonical_hash({
        "currency": currency,
        "discount_paise": discount_paise,
        "items": canonical_items,
        "merchant_id": merchant_id,
        "serialization_version": SERIALIZATION_VERSION,
        "shipping_paise": shipping_paise,
        "subtotal_paise": subtotal_paise,
        "tax_paise": tax_paise,
        "total_paise": total_paise,
        "warranty_months": warranty_months,
    })
