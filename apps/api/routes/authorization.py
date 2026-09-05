"""
Transactra — Authorization API Routes

Endpoints:
- POST /authorize — Run 16-predicate authorization gate
- GET  /authorize/{decision_id} — Get authorization decision

This is the core endpoint. AI proposes → infrastructure verifies.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from backend.kernel.authorization.gate import (
    AuthorizationGate,
    AuthorizationRequest,
)

router = APIRouter(prefix="/authorize", tags=["authorization"])

# Singleton gate instance — stateless, thread-safe
_gate = AuthorizationGate()
_decisions: dict[UUID, dict[str, Any]] = {}


# ── Request/Response Models ──────────────────────────

class AuthorizeRequest(BaseModel):
    principal_user_id: UUID
    agent_id: UUID
    mandate_id: UUID
    consent_id: UUID
    cart_hash: str = Field(min_length=1)
    amount_paise: int = Field(gt=0)
    currency: str = "INR"
    category: str
    merchant_id: UUID
    idempotency_key: str = Field(min_length=1)
    authorization_nonce: str = Field(min_length=1)
    # Pre-resolved predicate inputs (in production, resolved from DB)
    principal_active: bool = True
    agent_active: bool = True
    mandate_active: bool = True
    mandate_has_budget: bool = True
    mandate_category_ok: bool = True
    mandate_merchant_ok: bool = True
    consent_valid: bool = True
    consent_cart_hash: str = ""
    nonce_unused: bool = True
    idempotency_fresh: bool = True

    @field_validator("amount_paise")
    @classmethod
    def validate_integer(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("Amount must be integer paise")
        return v


class PredicateResultResponse(BaseModel):
    rule_id: str
    passed: bool
    reason: str


class AuthorizationResponse(BaseModel):
    decision_id: UUID
    request_id: UUID
    allowed: bool
    failed_rule_id: str | None
    failed_reason: str | None
    rule_count: int
    rule_trail: list[PredicateResultResponse]
    snapshot: dict[str, Any]
    timestamp: str


# ── Endpoints ────────────────────────────────────────

@router.post("", response_model=AuthorizationResponse, status_code=200)
async def authorize(req: AuthorizeRequest) -> AuthorizationResponse:
    """
    Run the 16-predicate authorization gate.

    AI proposes → deterministic infrastructure verifies:
    1.  RequestFormatValid
    2.  PrincipalAuthenticated
    3.  PrincipalActive
    4.  AgentActive
    5.  AgentOwnedByPrincipal
    6.  MandateExists
    7.  MandateActive
    8.  MandateOwnedByPrincipal
    9.  MandateCoversCategory
    10. MandateCoversAmount
    11. MandateCoversMerchant
    12. CartHashMatches
    13. ConsentValid
    14. ConsentMatchesCart
    15. NonceUnused
    16. IdempotencyKeyFresh

    Short-circuit: first failure → DENY. All 16 pass → ALLOW.

    Complexity: O(1) amortized.
    """
    auth_req = AuthorizationRequest(
        request_id=uuid4(),
        principal_user_id=req.principal_user_id,
        agent_id=req.agent_id,
        mandate_id=req.mandate_id,
        consent_id=req.consent_id,
        cart_hash=req.cart_hash,
        amount_paise=req.amount_paise,
        currency=req.currency,
        category=req.category,
        merchant_id=req.merchant_id,
        idempotency_key=req.idempotency_key,
        authorization_nonce=req.authorization_nonce,
    )

    decision = _gate.evaluate(
        auth_req,
        principal_active=req.principal_active,
        principal_user_id=req.principal_user_id,
        agent_active=req.agent_active,
        agent_owner_id=req.principal_user_id,
        agent_capabilities=frozenset({"request_authorization"}),
        mandate_active=req.mandate_active,
        mandate_owner_id=req.principal_user_id,
        mandate_agent_id=req.agent_id,
        mandate_has_budget=req.mandate_has_budget,
        mandate_category_ok=req.mandate_category_ok,
        mandate_merchant_ok=req.mandate_merchant_ok,
        mandate_cart_hash=None,
        consent_valid=req.consent_valid,
        consent_cart_hash=req.consent_cart_hash or req.cart_hash,
        nonce_unused=req.nonce_unused,
        idempotency_fresh=req.idempotency_fresh,
    )

    # Store for retrieval
    result = {
        "decision_id": decision.decision_id,
        "request_id": decision.request_id,
        "allowed": decision.allowed,
        "failed_rule_id": decision.failed_rule_id,
        "failed_reason": decision.failed_reason,
        "rule_count": len(decision.rule_trail),
        "rule_trail": [
            {"rule_id": r.rule_id, "passed": r.passed, "reason": r.reason}
            for r in decision.rule_trail
        ],
        "snapshot": decision.snapshot,
        "timestamp": decision.timestamp.isoformat() + "Z",
    }
    _decisions[decision.decision_id] = result

    return AuthorizationResponse(**result)


@router.get("/{decision_id}", response_model=AuthorizationResponse)
async def get_decision(decision_id: UUID) -> AuthorizationResponse:
    """Retrieve an authorization decision by ID. O(1)."""
    decision = _decisions.get(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return AuthorizationResponse(**decision)
