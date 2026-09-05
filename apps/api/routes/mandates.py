"""
Transactra — Mandate & Consent API Routes

Endpoints:
- POST /mandates — Create a spending mandate
- GET  /mandates/{id} — Get mandate details
- POST /mandates/{id}/consent — Request consent for a cart
- GET  /consents/{id} — Get consent status

All financial amounts in paise (integer). No float.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from apps.api.security import CurrentUser, get_current_user

router = APIRouter(prefix="/mandates", tags=["mandates"])


# ── Request/Response Models ──────────────────────────

class CreateMandateRequest(BaseModel):
    user_id: UUID
    agent_id: UUID
    mandate_type: str = Field(pattern="^(per_transaction|daily|weekly|monthly)$")
    max_amount_paise: int = Field(gt=0)
    currency: str = "INR"
    allowed_categories: list[str] | None = None
    allowed_merchant_ids: list[UUID] | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None

    @field_validator("max_amount_paise")
    @classmethod
    def validate_integer(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("Amount must be integer paise, not float")
        if v > 100_000_00_00:  # ₹10,00,000 cap
            raise ValueError("Amount exceeds maximum allowed (₹10,00,000)")
        return v


class MandateResponse(BaseModel):
    mandate_id: UUID
    user_id: UUID
    agent_id: UUID
    mandate_type: str
    status: str
    max_amount_paise: int
    used_amount_paise: int
    remaining_paise: int
    currency: str
    allowed_categories: list[str] | None
    allowed_merchant_ids: list[str] | None
    valid_from: datetime | None
    valid_until: datetime | None
    created_at: datetime


class CreateConsentRequest(BaseModel):
    user_id: UUID
    cart_hash: str = Field(min_length=1, max_length=64)
    amount_paise: int = Field(gt=0)
    currency: str = "INR"

    @field_validator("amount_paise")
    @classmethod
    def validate_integer(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("Amount must be integer paise, not float")
        return v


class ConsentResponse(BaseModel):
    consent_id: UUID
    user_id: UUID
    mandate_id: UUID
    cart_hash: str
    amount_paise: int
    currency: str
    status: str
    expires_at: datetime | None
    created_at: datetime


# ── In-memory store (for stateless demo; DB in production) ───

_mandates: dict[UUID, dict[str, Any]] = {}
_consents: dict[UUID, dict[str, Any]] = {}


# ── Endpoints ────────────────────────────────────────

@router.post("", response_model=MandateResponse, status_code=201)
async def create_mandate(
    req: CreateMandateRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> MandateResponse:
    """
    Create a spending mandate that bounds what an AI agent can spend.

    The mandate defines:
    - Maximum amount (in paise, integer only)
    - Allowed categories and merchants
    - Time window (valid_from to valid_until)

    Requires authentication. User can only create mandates for themselves.

    Complexity: O(1).
    """
    # Ownership check — user can only create mandates for themselves
    if str(req.user_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot create mandate for another user")
    mandate_id = uuid4()
    now = datetime.now(timezone.utc)

    mandate = {
        "mandate_id": mandate_id,
        "user_id": req.user_id,
        "agent_id": req.agent_id,
        "mandate_type": req.mandate_type,
        "status": "active",
        "max_amount_paise": req.max_amount_paise,
        "used_amount_paise": 0,
        "currency": req.currency,
        "allowed_categories": req.allowed_categories,
        "allowed_merchant_ids": [str(m) for m in req.allowed_merchant_ids] if req.allowed_merchant_ids else None,
        "valid_from": req.valid_from,
        "valid_until": req.valid_until,
        "created_at": now,
    }
    _mandates[mandate_id] = mandate

    return MandateResponse(
        **mandate,
        remaining_paise=req.max_amount_paise,
    )


@router.get("/{mandate_id}", response_model=MandateResponse)
async def get_mandate(
    mandate_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> MandateResponse:
    """Get mandate details. O(1) lookup. Requires authentication."""
    mandate = _mandates.get(mandate_id)
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    # Ownership check
    if str(mandate["user_id"]) != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return MandateResponse(
        **mandate,
        remaining_paise=mandate["max_amount_paise"] - mandate["used_amount_paise"],
    )


@router.post("/{mandate_id}/consent", response_model=ConsentResponse, status_code=201)
async def create_consent(
    mandate_id: UUID,
    req: CreateConsentRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> ConsentResponse:
    """
    Request user consent for a specific cart under a mandate.

    The consent is bound to the exact cart hash — if the cart changes,
    the consent is invalidated (INV-06).

    Complexity: O(1).
    """
    mandate = _mandates.get(mandate_id)
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    if mandate["status"] != "active":
        raise HTTPException(status_code=409, detail="Mandate is not active")
    if req.amount_paise > mandate["max_amount_paise"] - mandate["used_amount_paise"]:
        raise HTTPException(status_code=409, detail="Amount exceeds mandate budget")

    consent_id = uuid4()
    now = datetime.now(timezone.utc)

    consent = {
        "consent_id": consent_id,
        "user_id": req.user_id,
        "mandate_id": mandate_id,
        "cart_hash": req.cart_hash,
        "amount_paise": req.amount_paise,
        "currency": req.currency,
        "status": "approved",
        "expires_at": None,
        "created_at": now,
    }
    _consents[consent_id] = consent

    return ConsentResponse(**consent)


@router.get("/consent/{consent_id}", response_model=ConsentResponse)
async def get_consent(consent_id: UUID) -> ConsentResponse:
    """Get consent status. O(1) lookup."""
    consent = _consents.get(consent_id)
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    return ConsentResponse(**consent)
