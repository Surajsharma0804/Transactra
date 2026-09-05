"""
Transactra — Catalog API Routes

Search and retrieve products from the catalog.
All responses include search plan for transparency.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.retrieval.search import CatalogSearchService
from backend.kernel.domain.product import SearchFilters
from db.session import get_session

router = APIRouter(prefix="/catalog", tags=["catalog"])

_search_service = CatalogSearchService()


# ── Request / Response Models ────────────────────────

class SearchRequest(BaseModel):
    """Search request body for POST /catalog/search."""
    query: str | None = None
    categories: list[str] | None = None
    merchant_ids: list[UUID] | None = None
    min_price_paise: int | None = Field(None, ge=0)
    max_price_paise: int | None = Field(None, ge=0)
    warranty_min_months: int | None = Field(None, ge=0)
    refurbished_allowed: bool = True
    in_stock_only: bool = True
    attributes: dict | None = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ProductResponse(BaseModel):
    """Single product in search results."""
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
    relevance_score: float = 0.0

    class Config:
        from_attributes = True


class SearchPlanResponse(BaseModel):
    """Transparency: what the search engine did."""
    stage_1_sql_filters: dict
    stage_1_result_count: int
    stage_2_vector_used: bool
    stage_2_model_version: str | None
    stage_3_recheck_count: int
    total_candidates: int
    elapsed_ms: float


class SearchResponse(BaseModel):
    """Complete search response."""
    success: bool = True
    products: list[ProductResponse]
    total_count: int
    search_plan: SearchPlanResponse


# ── Routes ───────────────────────────────────────────

@router.post("/search", response_model=SearchResponse)
async def search_products(
    request: SearchRequest,
    session: AsyncSession = Depends(get_session),
) -> SearchResponse:
    """
    Three-stage search: SQL filter → vector rank → deterministic recheck.

    Complexity: O(log n + k + top_n · k_constraints).
    """
    filters = SearchFilters(
        merchant_ids=request.merchant_ids,
        categories=request.categories,
        min_price_paise=request.min_price_paise,
        max_price_paise=request.max_price_paise,
        warranty_min_months=request.warranty_min_months,
        refurbished_allowed=request.refurbished_allowed,
        in_stock_only=request.in_stock_only,
        attributes=request.attributes,
        limit=request.limit,
        offset=request.offset,
    )

    result = await _search_service.search(session, filters, request.query)

    return SearchResponse(
        products=[
            ProductResponse(
                product_id=p.product_id,
                merchant_id=p.merchant_id,
                sku=p.sku,
                title=p.title,
                description=p.description,
                category=p.category,
                price_paise=p.price_paise,
                currency=p.currency,
                attributes=p.attributes,
                warranty_months=p.warranty_months,
                refurbished=p.refurbished,
                shipping_days=p.shipping_days,
                shipping_paise=p.shipping_paise,
                returnable=p.returnable,
                return_window_days=p.return_window_days,
                available_quantity=p.available_quantity,
                relevance_score=p.relevance_score,
            )
            for p in result.products
        ],
        total_count=result.total_count,
        search_plan=SearchPlanResponse(
            stage_1_sql_filters=result.search_plan.stage_1_sql_filters,
            stage_1_result_count=result.search_plan.stage_1_result_count,
            stage_2_vector_used=result.search_plan.stage_2_vector_used,
            stage_2_model_version=result.search_plan.stage_2_model_version,
            stage_3_recheck_count=result.search_plan.stage_3_recheck_count,
            total_candidates=result.search_plan.total_candidates,
            elapsed_ms=result.search_plan.elapsed_ms,
        ),
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ProductResponse:
    """
    Get a single product by ID. O(1) primary key lookup.
    """
    product = await _search_service.get_product(session, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductResponse(
        product_id=product.product_id,
        merchant_id=product.merchant_id,
        sku=product.sku,
        title=product.title,
        description=product.description,
        category=product.category,
        price_paise=product.price_paise,
        currency=product.currency,
        attributes=product.attributes,
        warranty_months=product.warranty_months,
        refurbished=product.refurbished,
        shipping_days=product.shipping_days,
        shipping_paise=product.shipping_paise,
        returnable=product.returnable,
        return_window_days=product.return_window_days,
        available_quantity=product.available_quantity,
        relevance_score=product.relevance_score,
    )
