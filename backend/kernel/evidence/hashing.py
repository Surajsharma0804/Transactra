"""
Transactra — Canonical JSON Serialization

Deterministic JSON serialization for hashing and proof verification.
See algorithm specification in implementation_plan.md Section 17.
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
    Rejects: float (forbidden for monetary values).
    Complexity: O(1) per value.
    """
    if isinstance(obj, UUID):
        return str(obj).lower()

    if isinstance(obj, datetime):
        utc_dt = obj.astimezone(timezone.utc) if obj.tzinfo else obj
        if utc_dt.microsecond:
            return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc_dt.microsecond:06d}".rstrip("0") + "Z"
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    if isinstance(obj, float):
        raise ValueError(
            f"Float values are prohibited in canonical serialization: {obj}. "
            f"Use integer paise for monetary values."
        )

    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _reject_floats(obj: object, path: str = "$") -> None:
    """
    Pre-validate: reject any float values in the input.
    json.dumps handles float natively and never calls `default`,
    so we must check before serialization.
    Complexity: O(n) where n = total values in the dict.
    """
    if isinstance(obj, float):
        raise ValueError(
            f"Float values are prohibited in canonical serialization at {path}: {obj}. "
            f"Use integer paise for monetary values."
        )
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _reject_floats(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _reject_floats(v, f"{path}[{i}]")


def canonical_json(obj: dict) -> str:
    """
    Deterministic canonical JSON string.
    Same logical data → same string, always.
    Rejects floats (pre-validation).
    Complexity: O(n log n) key sort, O(n) output.
    """
    _reject_floats(obj)
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        default=_canonical_serializer,
        ensure_ascii=True,
    )


def canonical_hash(obj: dict) -> str:
    """SHA-256 of canonical JSON. Returns 64-char lowercase hex."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


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
    Canonical cart hash for exact-cart binding.
    Any change to contents/prices/merchant produces a different hash.
    Complexity: O(n) where n = line items.
    """
    canonical_items = [
        {
            "discount_paise": item["discount_paise"],
            "line_total_paise": item["line_total_paise"],
            "product_id": str(item["product_id"]).lower(),
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
