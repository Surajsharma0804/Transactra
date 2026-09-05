"""
Transactra — Canonical Hashing Tests

Validates:
- Deterministic output (same input → same hash)
- Key ordering (alphabetical)
- UUID lowercase normalization
- Float rejection
- Cart hash changes on any modification
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from backend.kernel.evidence.hashing import (
    canonical_json,
    canonical_hash,
    compute_cart_hash,
)


class TestCanonicalJson:

    def test_deterministic(self) -> None:
        """Same dict → same string, always."""
        d = {"b": 1, "a": 2, "c": 3}
        assert canonical_json(d) == canonical_json(d)

    def test_keys_sorted(self) -> None:
        result = canonical_json({"z": 1, "a": 2, "m": 3})
        assert result == '{"a":2,"m":3,"z":1}'

    def test_no_whitespace(self) -> None:
        result = canonical_json({"key": "value"})
        assert " " not in result

    def test_null_preserved(self) -> None:
        result = canonical_json({"a": None})
        assert result == '{"a":null}'

    def test_uuid_lowercase(self) -> None:
        uid = UUID("550E8400-E29B-41D4-A716-446655440000")
        result = canonical_json({"id": uid})
        assert "550e8400-e29b-41d4-a716-446655440000" in result
        # No uppercase
        assert "550E8400" not in result

    def test_datetime_utc_z(self) -> None:
        dt = datetime(2025, 9, 5, 2, 41, 13, tzinfo=timezone.utc)
        result = canonical_json({"ts": dt})
        assert "2025-09-05T02:41:13Z" in result

    def test_float_raises(self) -> None:
        """Floats are PROHIBITED in canonical serialization."""
        with pytest.raises(ValueError, match="Float.*prohibited"):
            canonical_json({"amount": 99.5})

    def test_integers_no_decimal(self) -> None:
        result = canonical_json({"amount": 6800000})
        assert "6800000" in result
        assert "." not in result

    def test_nested_sorted(self) -> None:
        result = canonical_json({"outer": {"z": 1, "a": 2}})
        assert '"outer":{"a":2,"z":1}' in result

    def test_array_order_preserved(self) -> None:
        result = canonical_json({"arr": [3, 1, 2]})
        assert '"arr":[3,1,2]' in result


class TestCanonicalHash:

    def test_deterministic_hash(self) -> None:
        d = {"key": "value", "num": 42}
        h1 = canonical_hash(d)
        h2 = canonical_hash(d)
        assert h1 == h2

    def test_hash_is_64_hex(self) -> None:
        h = canonical_hash({"a": 1})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_different_input_different_hash(self) -> None:
        h1 = canonical_hash({"a": 1})
        h2 = canonical_hash({"a": 2})
        assert h1 != h2


class TestCartHash:

    def _sample_items(self) -> list[dict]:
        return [
            {
                "product_id": UUID("00000000-0000-0000-0000-000000000001"),
                "sku": "LAP-001",
                "quantity": 1,
                "unit_price_paise": 6_800_000,
                "discount_paise": 200_000,
                "line_total_paise": 6_600_000,
            }
        ]

    def test_deterministic(self) -> None:
        merchant = UUID("00000000-0000-0000-0000-000000000099")
        items = self._sample_items()
        h1 = compute_cart_hash(merchant, items, 6_600_000, 50_000, 1_197_000, 200_000, 7_647_000)
        h2 = compute_cart_hash(merchant, items, 6_600_000, 50_000, 1_197_000, 200_000, 7_647_000)
        assert h1 == h2

    def test_price_change_different_hash(self) -> None:
        """INV-06: Price change → different hash → consent invalid."""
        merchant = UUID("00000000-0000-0000-0000-000000000099")
        items_a = self._sample_items()
        items_b = self._sample_items()
        items_b[0]["unit_price_paise"] = 6_900_000
        items_b[0]["line_total_paise"] = 6_700_000

        h_a = compute_cart_hash(merchant, items_a, 6_600_000, 50_000, 0, 200_000, 6_450_000)
        h_b = compute_cart_hash(merchant, items_b, 6_700_000, 50_000, 0, 200_000, 6_550_000)
        assert h_a != h_b

    def test_quantity_change_different_hash(self) -> None:
        merchant = UUID("00000000-0000-0000-0000-000000000099")
        items_a = self._sample_items()
        items_b = self._sample_items()
        items_b[0]["quantity"] = 2
        items_b[0]["line_total_paise"] = 13_400_000

        h_a = compute_cart_hash(merchant, items_a, 6_600_000, 0, 0, 0, 6_600_000)
        h_b = compute_cart_hash(merchant, items_b, 13_400_000, 0, 0, 0, 13_400_000)
        assert h_a != h_b

    def test_merchant_change_different_hash(self) -> None:
        items = self._sample_items()
        h_a = compute_cart_hash(UUID("00000000-0000-0000-0000-000000000001"), items, 6_600_000, 0, 0, 0, 6_600_000)
        h_b = compute_cart_hash(UUID("00000000-0000-0000-0000-000000000002"), items, 6_600_000, 0, 0, 0, 6_600_000)
        assert h_a != h_b

    def test_shipping_change_different_hash(self) -> None:
        merchant = UUID("00000000-0000-0000-0000-000000000099")
        items = self._sample_items()
        h_a = compute_cart_hash(merchant, items, 6_600_000, 0, 0, 0, 6_600_000)
        h_b = compute_cart_hash(merchant, items, 6_600_000, 50_000, 0, 0, 6_650_000)
        assert h_a != h_b
