"""
Transactra — Evidence API Routes

Endpoints:
- GET  /evidence/{order_id}        — Get the full evidence chain for an order
- POST /evidence/{order_id}/verify — Re-run chain.verify() server-side

Wires the EvidenceChain from orders into a dedicated API surface
so the frontend verification UI can show per-record hash verification.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.api.security import CurrentUser, get_current_user
from apps.api.routes.orders import _evidence_chains

router = APIRouter(prefix="/evidence", tags=["evidence"])


# ── Response Models ──────────────────────────────────

class EvidenceRecordResponse(BaseModel):
    sequence: int
    event_type: str
    data: dict[str, Any]
    timestamp: str
    record_hash: str
    prev_hash: str


class EvidenceChainResponse(BaseModel):
    chain_id: UUID
    order_id: UUID
    length: int
    head_hash: str
    records: list[EvidenceRecordResponse]


class VerifyRecordResult(BaseModel):
    sequence: int
    event_type: str
    expected_hash: str
    actual_hash: str
    passed: bool


class VerifyChainResponse(BaseModel):
    chain_id: UUID
    order_id: UUID
    length: int
    chain_valid: bool
    message: str
    record_results: list[VerifyRecordResult]


# ── Endpoints ────────────────────────────────────────

@router.get("/{order_id}", response_model=EvidenceChainResponse)
async def get_evidence_chain(
    order_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> EvidenceChainResponse:
    """
    Get the full evidence chain for an order.

    Returns every record with its full SHA-256 hashes
    (not truncated, unlike the proof endpoint).

    Complexity: O(n) where n = chain length.
    """
    chain = _evidence_chains.get(order_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Evidence chain not found")

    records = [
        EvidenceRecordResponse(
            sequence=r.sequence,
            event_type=r.event_type,
            data=r.data,
            timestamp=r.timestamp.isoformat() + "Z",
            record_hash=r.record_hash,
            prev_hash=r.prev_hash,
        )
        for r in chain.records
    ]

    return EvidenceChainResponse(
        chain_id=chain.chain_id,
        order_id=order_id,
        length=chain.length,
        head_hash=chain.head_hash,
        records=records,
    )


@router.post("/{order_id}/verify", response_model=VerifyChainResponse)
async def verify_evidence_chain(
    order_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> VerifyChainResponse:
    """
    Re-run chain verification server-side.

    Recomputes every record hash from scratch and compares against stored.
    Returns per-record pass/fail so the UI can show which record broke.

    Complexity: O(n) where n = chain length.
    """
    chain = _evidence_chains.get(order_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Evidence chain not found")

    # Run built-in chain verification
    chain_valid, message = chain.verify()

    # Build per-record verification results
    # Re-compute hashes manually to show expected vs actual
    import hashlib
    import json

    record_results = []
    for i, record in enumerate(chain.records):
        # Recompute the expected hash for this record
        hash_input = json.dumps({
            "sequence": record.sequence,
            "event_type": record.event_type,
            "data": record.data,
            "timestamp": record.timestamp.isoformat(),
            "prev_hash": record.prev_hash,
        }, sort_keys=True, default=str)
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        record_results.append(VerifyRecordResult(
            sequence=record.sequence,
            event_type=record.event_type,
            expected_hash=expected_hash,
            actual_hash=record.record_hash,
            passed=expected_hash == record.record_hash,
        ))

    return VerifyChainResponse(
        chain_id=chain.chain_id,
        order_id=order_id,
        length=chain.length,
        chain_valid=chain_valid,
        message=message,
        record_results=record_results,
    )
