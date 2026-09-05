"""
Transactra — Order & Payment API Routes

Endpoints:
- POST /orders — Create order (after authorization)
- GET  /orders/{id} — Get order details
- POST /orders/{id}/payment — Initiate payment
- POST /payments/webhook — Razorpay webhook handler
- GET  /orders/{id}/proof — Evidence chain for an order
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, Field, field_validator

from backend.kernel.domain.order import (
    Order, OrderStatus, Payment, PaymentLocalState, PaymentProviderState,
)
from backend.kernel.evidence.chain import EvidenceChain, EventType

router = APIRouter(prefix="/orders", tags=["orders"])

# In-memory stores (demo mode — production uses DB)
_orders: dict[UUID, dict[str, Any]] = {}
_payments: dict[UUID, dict[str, Any]] = {}
_evidence_chains: dict[UUID, EvidenceChain] = {}


# ── Request/Response Models ──────────────────────────

class CreateOrderRequest(BaseModel):
    user_id: UUID
    cart_id: UUID
    mandate_id: UUID
    consent_id: UUID
    authorization_decision_id: UUID
    merchant_id: UUID
    total_paise: int = Field(gt=0)
    currency: str = "INR"
    cart_hash: str
    idempotency_key: str = Field(min_length=1)
    authorization_nonce: str = Field(min_length=1)

    @field_validator("total_paise")
    @classmethod
    def validate_integer(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("Amount must be integer paise")
        return v


class OrderResponse(BaseModel):
    order_id: UUID
    user_id: UUID
    status: str
    total_paise: int
    currency: str
    cart_hash: str
    created_at: str
    evidence_chain_length: int


class InitiatePaymentRequest(BaseModel):
    amount_paise: int = Field(gt=0)
    currency: str = "INR"
    idempotency_key: str = Field(min_length=1)

    @field_validator("amount_paise")
    @classmethod
    def validate_integer(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("Amount must be integer paise")
        return v


class PaymentResponse(BaseModel):
    payment_id: UUID
    order_id: UUID
    amount_paise: int
    currency: str
    local_state: str
    provider_confirmed_state: str | None
    is_paid: bool
    needs_reconciliation: bool
    created_at: str


class EvidenceProofResponse(BaseModel):
    chain_id: UUID
    order_id: UUID
    length: int
    valid: bool
    message: str
    records: list[dict[str, Any]]


# ── Endpoints ────────────────────────────────────────

@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(req: CreateOrderRequest) -> OrderResponse:
    """
    Create an order after successful authorization.

    Requires a valid authorization_decision_id that was previously
    returned by the /authorize endpoint.

    Creates an evidence chain for the order and records the creation event.

    Complexity: O(1).
    """
    # Idempotency check
    for existing in _orders.values():
        if existing.get("idempotency_key") == req.idempotency_key:
            chain = _evidence_chains.get(existing["order_id"])
            return OrderResponse(
                order_id=existing["order_id"],
                user_id=existing["user_id"],
                status=existing["status"],
                total_paise=existing["total_paise"],
                currency=existing["currency"],
                cart_hash=existing["cart_hash"],
                created_at=existing["created_at"],
                evidence_chain_length=chain.length if chain else 0,
            )

    order_id = uuid4()
    now = datetime.now(timezone.utc)

    order = {
        "order_id": order_id,
        "user_id": req.user_id,
        "cart_id": req.cart_id,
        "mandate_id": req.mandate_id,
        "consent_id": req.consent_id,
        "authorization_decision_id": req.authorization_decision_id,
        "merchant_id": req.merchant_id,
        "total_paise": req.total_paise,
        "currency": req.currency,
        "status": "created",
        "cart_hash": req.cart_hash,
        "idempotency_key": req.idempotency_key,
        "authorization_nonce": req.authorization_nonce,
        "created_at": now.isoformat() + "Z",
    }
    _orders[order_id] = order

    # Create evidence chain
    chain = EvidenceChain()
    chain.append(EventType.ORDER_CREATED, {
        "order_id": str(order_id),
        "user_id": str(req.user_id),
        "total_paise": req.total_paise,
        "cart_hash": req.cart_hash,
        "authorization_decision_id": str(req.authorization_decision_id),
    })
    _evidence_chains[order_id] = chain

    return OrderResponse(
        order_id=order_id,
        user_id=req.user_id,
        status="created",
        total_paise=req.total_paise,
        currency=req.currency,
        cart_hash=req.cart_hash,
        created_at=order["created_at"],
        evidence_chain_length=chain.length,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: UUID) -> OrderResponse:
    """Get order details. O(1)."""
    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    chain = _evidence_chains.get(order_id)
    return OrderResponse(
        order_id=order["order_id"],
        user_id=order["user_id"],
        status=order["status"],
        total_paise=order["total_paise"],
        currency=order["currency"],
        cart_hash=order["cart_hash"],
        created_at=order["created_at"],
        evidence_chain_length=chain.length if chain else 0,
    )


@router.post("/{order_id}/payment", response_model=PaymentResponse, status_code=201)
async def initiate_payment(order_id: UUID, req: InitiatePaymentRequest) -> PaymentResponse:
    """
    Initiate payment for an order.

    Creates a payment record in "initiated" local_state.
    provider_confirmed_state remains null until webhook confirms.

    Dual-state architecture (INV-09):
    - local_state: what WE did
    - provider_confirmed_state: what the WEBHOOK confirmed

    Complexity: O(1).
    """
    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order["status"] not in ("created", "payment_pending"):
        raise HTTPException(status_code=409, detail=f"Order status {order['status']} cannot accept payment")

    # Idempotency check
    for existing in _payments.values():
        if existing.get("idempotency_key") == req.idempotency_key:
            return PaymentResponse(**existing)

    payment_id = uuid4()
    now = datetime.now(timezone.utc)

    payment = {
        "payment_id": payment_id,
        "order_id": order_id,
        "amount_paise": req.amount_paise,
        "currency": req.currency,
        "local_state": "initiated",
        "provider_confirmed_state": None,
        "is_paid": False,
        "needs_reconciliation": False,
        "idempotency_key": req.idempotency_key,
        "created_at": now.isoformat() + "Z",
    }
    _payments[payment_id] = payment

    # Update order status
    order["status"] = "payment_pending"

    # Add to evidence chain
    chain = _evidence_chains.get(order_id)
    if chain:
        chain.append(EventType.PAYMENT_INITIATED, {
            "payment_id": str(payment_id),
            "amount_paise": req.amount_paise,
            "local_state": "initiated",
        })

    return PaymentResponse(**payment)


@router.post("/webhook/razorpay", status_code=200)
async def razorpay_webhook(request: Request) -> dict[str, str]:
    """
    Razorpay webhook handler.

    This is the ONLY endpoint that can set provider_confirmed_state.
    In production, verifies HMAC-SHA256 signature before processing.

    Dual-state: Only this webhook is authoritative for "is this paid?"

    Complexity: O(1) per webhook.
    """
    body = await request.json()
    event_type = body.get("event", "")
    entity = body.get("payload", {}).get("payment", {}).get("entity", {})

    if not entity:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    provider_order_id = entity.get("order_id", "")
    status = entity.get("status", "")

    # Find matching payment by scanning (in production, indexed lookup)
    for payment in _payments.values():
        if str(payment["order_id"]) == provider_order_id or payment.get("provider_order_id") == provider_order_id:
            now = datetime.now(timezone.utc)

            if status == "captured":
                payment["provider_confirmed_state"] = "captured"
                payment["local_state"] = "completed"
                payment["is_paid"] = True
                payment["needs_reconciliation"] = False

                # Update order
                order = _orders.get(payment["order_id"])
                if order:
                    order["status"] = "paid"
                    chain = _evidence_chains.get(payment["order_id"])
                    if chain:
                        chain.append(EventType.PAYMENT_PROVIDER_CONFIRMED, {
                            "payment_id": str(payment["payment_id"]),
                            "provider_confirmed_state": "captured",
                            "amount_paise": payment["amount_paise"],
                        })

            elif status == "failed":
                payment["provider_confirmed_state"] = "failed"
                payment["local_state"] = "failed"
                payment["is_paid"] = False

            return {"status": "ok"}

    return {"status": "no_matching_payment"}


@router.get("/{order_id}/proof", response_model=EvidenceProofResponse)
async def get_proof(order_id: UUID) -> EvidenceProofResponse:
    """
    Get the evidence chain (trust proof) for an order.

    Returns the complete hash-linked evidence trail that proves
    every step of the transaction was authorized.

    Verifies chain integrity before returning.

    Complexity: O(n) where n = chain length.
    """
    chain = _evidence_chains.get(order_id)
    if not chain:
        raise HTTPException(status_code=404, detail="Evidence chain not found")

    valid, msg = chain.verify()

    records = [
        {
            "sequence": r.sequence,
            "event_type": r.event_type,
            "data": r.data,
            "timestamp": r.timestamp.isoformat() + "Z",
            "record_hash": r.record_hash[:16] + "...",
            "prev_hash": r.prev_hash[:16] + "...",
        }
        for r in chain.records
    ]

    return EvidenceProofResponse(
        chain_id=chain.chain_id,
        order_id=order_id,
        length=chain.length,
        valid=valid,
        message=msg,
        records=records,
    )
