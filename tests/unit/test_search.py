"""
Transactra — Search Pipeline Unit Tests

Tests the deterministic parts of the search pipeline without DB:
- SearchFilters validation and bounds
- Stage 3 recheck correctness
- Attribute matching
- Edge cases

All O(1) per test — no DB, no network.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from backend.kernel.domain.product import ProductCandidate, SearchFilters
from adapters.retrieval.search import CatalogSearchService


# ── Helper to build ProductCandidate ─────────────────

def _make_candidate(
    price_paise: int = 6_800_000,
    category: str = "laptops",
    merchant_id: UUID | None = None,
    warranty_months: int = 12,
    refurbished: bool = False,
    available_quantity: int = 10,
    attributes: dict | None = None,
    sku: str = "LAP-001",
) -> ProductCandidate:
    return ProductCandidate(
        product_id=uuid4(),
        merchant_id=merchant_id or uuid4(),
        sku=sku,
        title="Test Product",
        description="Test description",
        category=category,
        price_paise=price_paise,
        currency="INR",
        attributes=attributes or {},
        warranty_months=warranty_months,
        refurbished=refurbished,
        shipping_days=3,
        shipping_paise=0,
        returnable=True,
        return_window_days=7,
        available_quantity=available_quantity,
    )


# ═══════════════════════════════════════════════════════
# SearchFilters Validation
# ═══════════════════════════════════════════════════════

class TestSearchFiltersValidation:

    def test_default_values(self) -> None:
        f = SearchFilters()
        assert f.limit == 20
        assert f.offset == 0
        assert f.in_stock_only is True
        assert f.refurbished_allowed is True

    def test_limit_clamped_to_100(self) -> None:
        f = SearchFilters(limit=200)
        assert f.limit == 100

    def test_limit_clamped_to_1(self) -> None:
        f = SearchFilters(limit=0)
        assert f.limit == 1

    def test_negative_offset_clamped(self) -> None:
        f = SearchFilters(offset=-5)
        assert f.offset == 0

    def test_all_filters(self) -> None:
        mid = uuid4()
        f = SearchFilters(
            merchant_ids=[mid],
            categories=["laptops"],
            min_price_paise=3_000_000,
            max_price_paise=10_000_000,
            warranty_min_months=12,
            refurbished_allowed=False,
            in_stock_only=True,
            attributes={"ram_gb": 16},
            limit=10,
            offset=20,
        )
        assert f.merchant_ids == [mid]
        assert f.categories == ["laptops"]
        assert f.min_price_paise == 3_000_000
        assert f.max_price_paise == 10_000_000


# ═══════════════════════════════════════════════════════
# Stage 3 Re-check
# ═══════════════════════════════════════════════════════

class TestStage3Recheck:
    """Stage 3 re-verifies every hard constraint. O(top_n · k_constraints)."""

    def setup_method(self) -> None:
        self.svc = CatalogSearchService()

    def test_all_pass(self) -> None:
        """All candidates pass recheck with default filters."""
        candidates = [_make_candidate() for _ in range(5)]
        filters = SearchFilters()
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 5

    def test_max_price_filter(self) -> None:
        """Recheck rejects candidates above max_price."""
        candidates = [
            _make_candidate(price_paise=5_000_000),
            _make_candidate(price_paise=8_000_000),
            _make_candidate(price_paise=12_000_000),
        ]
        filters = SearchFilters(max_price_paise=10_000_000)
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2
        assert all(c.price_paise <= 10_000_000 for c in result)

    def test_min_price_filter(self) -> None:
        candidates = [
            _make_candidate(price_paise=2_000_000),
            _make_candidate(price_paise=5_000_000),
            _make_candidate(price_paise=8_000_000),
        ]
        filters = SearchFilters(min_price_paise=4_000_000)
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2
        assert all(c.price_paise >= 4_000_000 for c in result)

    def test_price_range_filter(self) -> None:
        candidates = [
            _make_candidate(price_paise=2_000_000),
            _make_candidate(price_paise=5_000_000),
            _make_candidate(price_paise=8_000_000),
            _make_candidate(price_paise=12_000_000),
        ]
        filters = SearchFilters(min_price_paise=4_000_000, max_price_paise=10_000_000)
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2

    def test_warranty_filter(self) -> None:
        candidates = [
            _make_candidate(warranty_months=6),
            _make_candidate(warranty_months=12),
            _make_candidate(warranty_months=24),
        ]
        filters = SearchFilters(warranty_min_months=12)
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2

    def test_refurbished_excluded(self) -> None:
        """When refurbished_allowed=False, refurbished items are filtered out."""
        candidates = [
            _make_candidate(refurbished=False),
            _make_candidate(refurbished=True),
            _make_candidate(refurbished=False),
        ]
        filters = SearchFilters(refurbished_allowed=False)
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2
        assert all(not c.refurbished for c in result)

    def test_refurbished_allowed(self) -> None:
        """When refurbished_allowed=True (default), all items pass."""
        candidates = [
            _make_candidate(refurbished=True),
            _make_candidate(refurbished=False),
        ]
        filters = SearchFilters(refurbished_allowed=True)
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2

    def test_out_of_stock_excluded(self) -> None:
        """In-stock-only excludes zero-available items."""
        candidates = [
            _make_candidate(available_quantity=10),
            _make_candidate(available_quantity=0),
            _make_candidate(available_quantity=5),
        ]
        filters = SearchFilters(in_stock_only=True)
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2

    def test_out_of_stock_included_when_allowed(self) -> None:
        candidates = [
            _make_candidate(available_quantity=10),
            _make_candidate(available_quantity=0),
        ]
        filters = SearchFilters(in_stock_only=False)
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2

    def test_category_filter(self) -> None:
        candidates = [
            _make_candidate(category="laptops"),
            _make_candidate(category="smartphones"),
            _make_candidate(category="laptops"),
        ]
        filters = SearchFilters(categories=["laptops"])
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2

    def test_multi_category_filter(self) -> None:
        candidates = [
            _make_candidate(category="laptops"),
            _make_candidate(category="smartphones"),
            _make_candidate(category="audio"),
        ]
        filters = SearchFilters(categories=["laptops", "audio"])
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2

    def test_merchant_filter(self) -> None:
        mid1 = uuid4()
        mid2 = uuid4()
        candidates = [
            _make_candidate(merchant_id=mid1),
            _make_candidate(merchant_id=mid2),
            _make_candidate(merchant_id=mid1),
        ]
        filters = SearchFilters(merchant_ids=[mid1])
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 2

    def test_combined_filters(self) -> None:
        """Multiple filters applied together — all must pass."""
        mid = uuid4()
        candidates = [
            _make_candidate(price_paise=5_000_000, category="laptops", merchant_id=mid, warranty_months=12),
            _make_candidate(price_paise=5_000_000, category="laptops", merchant_id=mid, warranty_months=3),
            _make_candidate(price_paise=5_000_000, category="phones", merchant_id=mid, warranty_months=12),
            _make_candidate(price_paise=15_000_000, category="laptops", merchant_id=mid, warranty_months=12),
        ]
        filters = SearchFilters(
            max_price_paise=10_000_000,
            categories=["laptops"],
            warranty_min_months=12,
            merchant_ids=[mid],
        )
        result = self.svc._stage3_recheck(candidates, filters)
        assert len(result) == 1

    def test_empty_candidates(self) -> None:
        filters = SearchFilters()
        result = self.svc._stage3_recheck([], filters)
        assert result == []


# ═══════════════════════════════════════════════════════
# Attribute Matching
# ═══════════════════════════════════════════════════════

class TestAttributeMatching:
    """Tests JSONB @> equivalent in application layer. O(a)."""

    def test_exact_match(self) -> None:
        assert CatalogSearchService._attributes_match(
            {"brand": "TechMart", "ram_gb": 16},
            {"brand": "TechMart"},
        )

    def test_multiple_attributes(self) -> None:
        assert CatalogSearchService._attributes_match(
            {"brand": "TechMart", "ram_gb": 16, "gpu": "RTX 4070"},
            {"brand": "TechMart", "ram_gb": 16},
        )

    def test_no_match(self) -> None:
        assert not CatalogSearchService._attributes_match(
            {"brand": "TechMart", "ram_gb": 8},
            {"ram_gb": 16},
        )

    def test_missing_key(self) -> None:
        assert not CatalogSearchService._attributes_match(
            {"brand": "TechMart"},
            {"gpu": "RTX 4070"},
        )

    def test_empty_filter(self) -> None:
        assert CatalogSearchService._attributes_match(
            {"brand": "TechMart", "ram_gb": 16},
            {},
        )

    def test_empty_product_attrs(self) -> None:
        assert not CatalogSearchService._attributes_match(
            {},
            {"brand": "TechMart"},
        )

    def test_attribute_recheck_in_stage3(self) -> None:
        """Stage 3 uses attribute matching for JSONB containment recheck."""
        svc = CatalogSearchService()
        candidates = [
            _make_candidate(attributes={"brand": "TechMart", "ram_gb": 16}),
            _make_candidate(attributes={"brand": "TechMart", "ram_gb": 8}),
            _make_candidate(attributes={"brand": "GadgetWorld", "ram_gb": 16}),
        ]
        filters = SearchFilters(attributes={"brand": "TechMart", "ram_gb": 16})
        result = svc._stage3_recheck(candidates, filters)
        assert len(result) == 1


# ═══════════════════════════════════════════════════════
# ProductCandidate Immutability
# ═══════════════════════════════════════════════════════

class TestProductCandidate:

    def test_frozen(self) -> None:
        c = _make_candidate()
        with pytest.raises(AttributeError):
            c.price_paise = 0  # type: ignore[misc]

    def test_default_relevance(self) -> None:
        c = _make_candidate()
        assert c.relevance_score == 0.0
