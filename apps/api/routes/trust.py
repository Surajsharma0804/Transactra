"""
Transactra — Trust Score API Routes

Endpoints:
- GET  /trust/{merchant_id} — Get computed trust evidence for one merchant
- GET  /trust               — Get all merchants' trust scores
- POST /trust/{merchant_id}/event — Record a trust-relevant event

Wires the TrustEngine (backend/kernel/domain/trust.py) to HTTP.
All scores are computed from evidence, not self-declared.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.api.security import CurrentUser, get_current_user
from backend.kernel.domain.trust import TrustEvidence, get_trust_engine

router = APIRouter(prefix="/trust", tags=["trust"])


# ── Response Models ──────────────────────────────────

class TrustScoreResponse(BaseModel):
    merchant_id: str
    trust_score: float
    fulfillment_rate: float
    on_time_rate: float
    dispute_rate: float
    chain_integrity_rate: float
    total_orders: int
    completed_orders: int
    computed_at: str


class TrustEventRequest(BaseModel):
    event_type: str = Field(pattern="^(order_created|order_completed|dispute|chain_verified|chain_broken)$")
    fulfillment_hours: float | None = None
    was_on_time: bool | None = None


# ── Endpoints ────────────────────────────────────────

@router.get(
    "/{merchant_id}",
    response_model=TrustScoreResponse,
    summary="Get merchant trust score",
)
async def get_trust_score(
    merchant_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> TrustScoreResponse:
    """
    Compute and return trust evidence for a merchant.

    Trust is computed from real order data — fulfillment rate,
    on-time delivery, dispute rate, and evidence chain integrity.

    O(1) computation from pre-aggregated stats.
    """
    engine = get_trust_engine()
    evidence = engine.compute_trust(merchant_id)
    return TrustScoreResponse(**evidence.to_dict())


@router.get(
    "",
    response_model=list[TrustScoreResponse],
    summary="Get all trust scores",
)
async def get_all_trust_scores(
    current_user: CurrentUser = Depends(get_current_user),
) -> list[TrustScoreResponse]:
    """
    Compute trust scores for all known merchants.

    O(m) where m = number of merchants with recorded events.
    """
    engine = get_trust_engine()
    all_evidence = engine.get_all_trust_scores()
    return [TrustScoreResponse(**e.to_dict()) for e in all_evidence]


@router.post(
    "/{merchant_id}/event",
    response_model=TrustScoreResponse,
    status_code=201,
    summary="Record trust event",
)
async def record_trust_event(
    merchant_id: UUID,
    req: TrustEventRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> TrustScoreResponse:
    """
    Record a trust-relevant event for a merchant.

    Events:
    - order_created: New order placed
    - order_completed: Order successfully fulfilled
    - dispute: Dispute filed
    - chain_verified: Evidence chain passed verification
    - chain_broken: Evidence chain failed verification

    O(1) per event.
    """
    engine = get_trust_engine()

    if req.event_type == "order_created":
        engine.record_order_created(merchant_id)
    elif req.event_type == "order_completed":
        engine.record_order_completed(
            merchant_id,
            fulfillment_hours=req.fulfillment_hours or 24.0,
            was_on_time=req.was_on_time if req.was_on_time is not None else True,
        )
    elif req.event_type == "dispute":
        engine.record_dispute(merchant_id)
    elif req.event_type == "chain_verified":
        engine.record_chain_verification(merchant_id, passed=True)
    elif req.event_type == "chain_broken":
        engine.record_chain_verification(merchant_id, passed=False)

    evidence = engine.compute_trust(merchant_id)
    return TrustScoreResponse(**evidence.to_dict())
