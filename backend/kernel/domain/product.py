"""
Transactra — Product Domain Types

Pure domain types for products, search filters, and search results.
No framework imports — used by both search adapter and API layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProductCandidate:
    """
    Product as returned from search. Immutable snapshot of catalog state.
    Contains only buyer-visible fields — no private merchant economics.
    """
    product_id: UUID
    merchant_id: UUID
    sku: str
    title: str
    description: str
    category: str
    price_paise: int
    currency: str
    attributes: dict
    warranty_months: int
    refurbished: bool
    shipping_days: int
    shipping_paise: int
    returnable: bool
    return_window_days: int
    available_quantity: int
    relevance_score: float = 0.0  # set by ranking stage


@dataclass(frozen=True, slots=True)
class SearchFilters:
    """
    Structured search filters. All optional.
    Used in Stage 1 (SQL hard filtering).

    Complexity of filter application:
    - Category/merchant IN: O(k) where k = filter list size
    - Price range: O(1) comparison
    - Warranty/refurbished: O(1) comparison
    - Attributes: O(a) JSONB containment via GIN index
    - In-stock: O(1) via generated column
    """
    merchant_ids: list[UUID] | None = None
    categories: list[str] | None = None
    min_price_paise: int | None = None
    max_price_paise: int | None = None
    warranty_min_months: int | None = None
    refurbished_allowed: bool = True
    in_stock_only: bool = True
    attributes: dict | None = None
    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 100:
            object.__setattr__(self, "limit", max(1, min(100, self.limit)))
        if self.offset < 0:
            object.__setattr__(self, "offset", 0)


@dataclass(frozen=True, slots=True)
class SearchPlan:
    """Explains what the search engine did — for debugging and transparency."""
    stage_1_sql_filters: dict
    stage_1_result_count: int
    stage_2_vector_used: bool
    stage_2_model_version: str | None
    stage_3_recheck_count: int
    total_candidates: int
    elapsed_ms: float


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Complete search result with candidates and plan."""
    products: list[ProductCandidate]
    total_count: int
    search_plan: SearchPlan
