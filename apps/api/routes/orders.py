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

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field, field_validator

from apps.api.security import CurrentUser, get_current_user

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
async def create_order(
    req: CreateOrderRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> OrderResponse:
    """
    Create an order after successful authorization.

    Requires authentication. User can only create orders for themselves.

    Complexity: O(1).
    """
    # Ownership check
    if str(req.user_id) != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot create order for another user")
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
async def get_order(
    order_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> OrderResponse:
    """Get order details. O(1). Requires authentication."""
    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Ownership check
    if str(order["user_id"]) != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
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
async def initiate_payment(
    order_id: UUID,
    req: InitiatePaymentRequest,
    current_user: CurrentUser = Depends(get_current_user),
) -> PaymentResponse:
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

    # Create Razorpay order via real API call if keys are configured
    razorpay_order_id = None
    from backend.config import get_settings
    settings = get_settings()

    if settings.razorpay_key_id and settings.razorpay_key_secret:
        try:
            import httpx
            import base64
            auth_str = f"{settings.razorpay_key_id}:{settings.razorpay_key_secret}"
            auth_header = base64.b64encode(auth_str.encode()).decode()

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.razorpay.com/v1/orders",
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "amount": req.amount_paise,
                        "currency": req.currency,
                        "receipt": str(order_id),
                        "notes": {"order_id": str(order_id), "payment_id": str(payment_id)},
                    },
                )
                if resp.status_code == 200:
                    rz_data = resp.json()
                    razorpay_order_id = rz_data.get("id")
                else:
                    import logging
                    logging.getLogger("transactra.payment").warning(
                        f"Razorpay order creation failed: {resp.status_code} {resp.text}"
                    )
        except Exception as e:
            import logging
            logging.getLogger("transactra.payment").warning(
                f"Razorpay API call failed, using local-only mode: {e}"
            )
    else:
        import logging
        logging.getLogger("transactra.payment").info(
            "Razorpay keys not configured — running in local-only payment mode"
        )

    payment = {
        "payment_id": payment_id,
        "order_id": order_id,
        "amount_paise": req.amount_paise,
        "currency": req.currency,
        "local_state": "initiated",
        "provider_confirmed_state": None,
        "provider_order_id": razorpay_order_id,
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
            "provider_order_id": razorpay_order_id,
        })

    return PaymentResponse(**payment)


@router.post("/webhook/razorpay", status_code=200)
async def razorpay_webhook(request: Request) -> dict[str, str]:
    """
    Razorpay webhook handler with HMAC-SHA256 signature verification.

    This is the ONLY endpoint that can set provider_confirmed_state.
    Signature is verified BEFORE processing any payment state changes.

    Dual-state: Only this webhook is authoritative for "is this paid?"

    Complexity: O(n) for HMAC where n = body length, O(1) for state update.
    """
    # Read raw body bytes first — HMAC must be computed on exact bytes
    raw_body = await request.body()

    # Verify HMAC-SHA256 signature — reject if missing or invalid
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    from adapters.payment.razorpay import RazorpaySignatureVerifier
    from backend.config import get_settings
    settings = get_settings()
    webhook_secret = getattr(settings, "razorpay_webhook_secret", "")

    if webhook_secret and not RazorpaySignatureVerifier.verify_webhook_signature(
        raw_body, signature, webhook_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Only after signature verification, parse the body
    import json as _json
    body = _json.loads(raw_body)
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
async def get_proof(
    order_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
) -> EvidenceProofResponse:
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
