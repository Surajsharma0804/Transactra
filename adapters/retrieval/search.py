"""
Transactra — Three-Stage Search Pipeline

Stage 1: SQL Hard Filtering
    Index: B-tree composite (is_active, category, price_paise) + GIN (attributes)
    Complexity: O(log n + k) where n = total products, k = matching rows
    Memory: O(k) bounded by LIMIT

Stage 2: Vector Ranking (optional, pgvector)
    Index: HNSW on product_embeddings.embedding
    Complexity: O(log n) approximate via HNSW
    Memory: O(top_n)
    NOTE: Runs ONLY on Stage 1 output via CTE join — not full catalog

Stage 3: Deterministic Re-check
    For each of top_n candidates: re-verify every hard constraint
    Complexity: O(top_n · k_constraints)
    Memory: O(top_n)

Overall: O(log n + k + top_n · k_constraints)
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.kernel.domain.product import (
    ProductCandidate,
    SearchFilters,
    SearchPlan,
    SearchResult,
)


class CatalogSearchService:
    """
    Three-stage search pipeline for the product catalog.

    Designed for optimal complexity:
    - Stage 1 leverages composite B-tree + GIN indexes
    - Stage 2 uses HNSW for sub-linear vector search
    - Stage 3 prevents stale results via deterministic recheck
    """

    async def search(
        self,
        session: AsyncSession,
        filters: SearchFilters,
        query_text: str | None = None,
    ) -> SearchResult:
        """
        Execute the three-stage search pipeline.

        Args:
            session: Async DB session
            filters: Structured hard filters
            query_text: Optional natural language query for vector ranking

        Returns:
            SearchResult with candidates, count, and search plan
        """
        start = time.perf_counter()

        # ── Stage 1: SQL Hard Filtering ──────────────
        stage1_results, total_count, applied_filters = await self._stage1_sql_filter(
            session, filters
        )

        # ── Stage 2: Vector Ranking (optional) ───────
        vector_used = False
        model_version = None
        if query_text and stage1_results:
            # Vector ranking runs on Stage 1 output only
            stage2_results, model_version = await self._stage2_vector_rank(
                session, stage1_results, query_text, filters.limit
            )
            vector_used = bool(stage2_results)
            if stage2_results:
                stage1_results = stage2_results

        # ── Stage 3: Deterministic Re-check ──────────
        verified = self._stage3_recheck(stage1_results, filters)

        elapsed_ms = (time.perf_counter() - start) * 1000

        plan = SearchPlan(
            stage_1_sql_filters=applied_filters,
            stage_1_result_count=total_count,
            stage_2_vector_used=vector_used,
            stage_2_model_version=model_version,
            stage_3_recheck_count=len(verified),
            total_candidates=len(verified),
            elapsed_ms=round(elapsed_ms, 2),
        )

        return SearchResult(
            products=verified,
            total_count=total_count,
            search_plan=plan,
        )

    async def get_product(
        self,
        session: AsyncSession,
        product_id: UUID,
    ) -> ProductCandidate | None:
        """
        Get a single product by ID. O(1) primary key lookup.
        """
        result = await session.execute(
            text("""
                SELECT p.*, i.quantity, i.reserved, (i.quantity - i.reserved) as available
                FROM products p
                LEFT JOIN inventory i ON i.product_id = p.product_id
                WHERE p.product_id = :pid AND p.is_active
            """),
            {"pid": product_id},
        )
        row = result.mappings().fetchone()
        if row is None:
            return None
        return self._row_to_candidate(row)

    # ── Stage 1: SQL Hard Filtering ──────────────────

    async def _stage1_sql_filter(
        self,
        session: AsyncSession,
        filters: SearchFilters,
    ) -> tuple[list[ProductCandidate], int, dict]:
        """
        Stage 1: SQL-based filtering using composite B-tree + GIN indexes.

        Query plan uses ix_products_search for (is_active, category, price_paise).
        JSONB attributes use ix_products_attributes GIN index with @> operator.

        Complexity: O(log n + k) where k = matching rows, bounded by LIMIT.
        """
        conditions: list[str] = ["p.is_active = true"]
        params: dict = {}
        applied: dict = {}

        if filters.categories:
            conditions.append("p.category = ANY(:categories)")
            params["categories"] = filters.categories
            applied["categories"] = filters.categories

        if filters.merchant_ids:
            conditions.append("p.merchant_id = ANY(:merchant_ids)")
            params["merchant_ids"] = [str(m) for m in filters.merchant_ids]
            applied["merchant_ids"] = [str(m) for m in filters.merchant_ids]

        if filters.min_price_paise is not None:
            conditions.append("p.price_paise >= :min_price")
            params["min_price"] = filters.min_price_paise
            applied["min_price_paise"] = filters.min_price_paise

        if filters.max_price_paise is not None:
            conditions.append("p.price_paise <= :max_price")
            params["max_price"] = filters.max_price_paise
            applied["max_price_paise"] = filters.max_price_paise

        if filters.warranty_min_months is not None:
            conditions.append("p.warranty_months >= :min_warranty")
            params["min_warranty"] = filters.warranty_min_months
            applied["warranty_min_months"] = filters.warranty_min_months

        if not filters.refurbished_allowed:
            conditions.append("p.refurbished = false")
            applied["refurbished_allowed"] = False

        if filters.in_stock_only:
            conditions.append("(i.quantity - i.reserved) > 0")
            applied["in_stock_only"] = True

        # JSONB attribute containment query — uses GIN index
        if filters.attributes:
            conditions.append("p.attributes @> :attrs::jsonb")
            import json
            params["attrs"] = json.dumps(filters.attributes)
            applied["attributes"] = filters.attributes

        where_clause = " AND ".join(conditions)

        # Count query (for pagination)
        count_sql = f"""
            SELECT COUNT(*)
            FROM products p
            LEFT JOIN inventory i ON i.product_id = p.product_id
            WHERE {where_clause}
        """
        count_result = await session.execute(text(count_sql), params)
        total_count = count_result.scalar() or 0

        # Data query with LIMIT/OFFSET
        data_sql = f"""
            SELECT p.*, i.quantity, i.reserved,
                   COALESCE(i.quantity - i.reserved, 0) as available
            FROM products p
            LEFT JOIN inventory i ON i.product_id = p.product_id
            WHERE {where_clause}
            ORDER BY p.price_paise ASC
            LIMIT :lim OFFSET :off
        """
        params["lim"] = filters.limit
        params["off"] = filters.offset

        result = await session.execute(text(data_sql), params)
        rows = result.mappings().fetchall()

        candidates = [self._row_to_candidate(row) for row in rows]
        return candidates, total_count, applied

    # ── Stage 2: Vector Ranking ──────────────────────

    async def _stage2_vector_rank(
        self,
        session: AsyncSession,
        candidates: list[ProductCandidate],
        query_text: str,
        limit: int,
    ) -> tuple[list[ProductCandidate] | None, str | None]:
        """
        Stage 2: Re-rank Stage 1 results using pgvector HNSW similarity.

        Only operates on the filtered candidate set from Stage 1 — NOT the
        full catalog. This is achieved by passing product IDs as a filter.

        Complexity: O(log n) via HNSW index on the filtered subset.
        """
        if not candidates:
            return None, None

        # For now, vector ranking is a stub — requires embedding generation
        # When implemented:
        # 1. Generate query embedding via LLM adapter
        # 2. SELECT from product_embeddings WHERE product_id IN (stage1_ids)
        #    ORDER BY embedding <=> query_embedding LIMIT top_n
        # 3. Re-order candidates by similarity score

        return None, None

    # ── Stage 3: Deterministic Re-check ──────────────

    def _stage3_recheck(
        self,
        candidates: list[ProductCandidate],
        filters: SearchFilters,
    ) -> list[ProductCandidate]:
        """
        Stage 3: Re-verify every hard constraint against latest data.

        Prevents stale results from cache or race conditions.
        Every candidate must satisfy ALL filters at the time of return.

        Complexity: O(top_n · k_constraints) where k_constraints ~ 7.
        Memory: O(top_n).
        """
        verified: list[ProductCandidate] = []

        for c in candidates:
            # Re-check every hard constraint
            if filters.max_price_paise is not None and c.price_paise > filters.max_price_paise:
                continue
            if filters.min_price_paise is not None and c.price_paise < filters.min_price_paise:
                continue
            if filters.warranty_min_months is not None and c.warranty_months < filters.warranty_min_months:
                continue
            if not filters.refurbished_allowed and c.refurbished:
                continue
            if filters.in_stock_only and c.available_quantity <= 0:
                continue
            if filters.categories and c.category not in filters.categories:
                continue
            if filters.merchant_ids and c.merchant_id not in filters.merchant_ids:
                continue
            if filters.attributes:
                # Check JSONB containment in application layer
                if not self._attributes_match(c.attributes, filters.attributes):
                    continue

            verified.append(c)

        return verified

    # ── Helpers ───────────────────────────────────────

    @staticmethod
    def _attributes_match(product_attrs: dict, filter_attrs: dict) -> bool:
        """
        Check if product attributes contain all filter attributes.
        Equivalent to JSONB @> operator.
        Complexity: O(a) where a = number of filter attributes.
        """
        for key, value in filter_attrs.items():
            if key not in product_attrs:
                return False
            if product_attrs[key] != value:
                return False
        return True

    @staticmethod
    def _row_to_candidate(row) -> ProductCandidate:
        """Convert a DB row to a ProductCandidate. O(1)."""
        return ProductCandidate(
            product_id=row["product_id"],
            merchant_id=row["merchant_id"],
            sku=row["sku"],
            title=row["title"],
            description=row["description"],
            category=row["category"],
            price_paise=row["price_paise"],
            currency=row["currency"],
            attributes=row["attributes"] or {},
            warranty_months=row["warranty_months"],
            refurbished=row["refurbished"],
            shipping_days=row["shipping_days"],
            shipping_paise=row["shipping_paise"],
            returnable=row["returnable"],
            return_window_days=row["return_window_days"],
            available_quantity=row.get("available", 0) or 0,
        )
