"""
Transactra — API Integration Tests

Tests the full HTTP API flow:
- Health check
- Mandate creation → Consent → Authorization → Order → Payment → Proof
- MCP tool listing and invocation with capability checks
- Error handling (404, 409, validation)

Uses FastAPI TestClient (no actual server needed).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ═══════════════════════════════════════════════════════
# Health & Root
# ═══════════════════════════════════════════════════════

class TestHealth:

    def test_health(self, client) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root(self, client) -> None:
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["name"] == "Transactra"

    def test_correlation_id_generated(self, client) -> None:
        r = client.get("/health")
        assert "x-correlation-id" in r.headers

    def test_correlation_id_echoed(self, client) -> None:
        r = client.get("/health", headers={"X-Correlation-ID": "test-123"})
        assert r.headers["x-correlation-id"] == "test-123"

    def test_timing_header(self, client) -> None:
        r = client.get("/health")
        assert "x-process-time-ms" in r.headers


# ═══════════════════════════════════════════════════════
# Mandate API
# ═══════════════════════════════════════════════════════

class TestMandateAPI:

    def test_create_mandate(self, client) -> None:
        r = client.post("/api/v1/mandates", json={
            "user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_type": "per_transaction",
            "max_amount_paise": 10_000_000,
        })
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "active"
        assert data["max_amount_paise"] == 10_000_000
        assert data["remaining_paise"] == 10_000_000

    def test_get_mandate(self, client) -> None:
        create = client.post("/api/v1/mandates", json={
            "user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_type": "daily",
            "max_amount_paise": 5_000_000,
        })
        mandate_id = create.json()["mandate_id"]
        r = client.get(f"/api/v1/mandates/{mandate_id}")
        assert r.status_code == 200
        assert r.json()["max_amount_paise"] == 5_000_000

    def test_mandate_not_found(self, client) -> None:
        r = client.get(f"/api/v1/mandates/{uuid4()}")
        assert r.status_code == 404

    def test_create_consent(self, client) -> None:
        mandate = client.post("/api/v1/mandates", json={
            "user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_type": "per_transaction",
            "max_amount_paise": 10_000_000,
        })
        mandate_id = mandate.json()["mandate_id"]
        user_id = mandate.json()["user_id"]

        r = client.post(f"/api/v1/mandates/{mandate_id}/consent", json={
            "user_id": user_id,
            "cart_hash": "abc123def456",
            "amount_paise": 6_800_000,
        })
        assert r.status_code == 201
        assert r.json()["status"] == "approved"
        assert r.json()["cart_hash"] == "abc123def456"

    def test_consent_exceeds_budget(self, client) -> None:
        mandate = client.post("/api/v1/mandates", json={
            "user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_type": "per_transaction",
            "max_amount_paise": 1_000_000,
        })
        mandate_id = mandate.json()["mandate_id"]

        r = client.post(f"/api/v1/mandates/{mandate_id}/consent", json={
            "user_id": str(uuid4()),
            "cart_hash": "abc",
            "amount_paise": 5_000_000,
        })
        assert r.status_code == 409


# ═══════════════════════════════════════════════════════
# Authorization API
# ═══════════════════════════════════════════════════════

class TestAuthorizationAPI:

    def test_authorize_allow(self, client) -> None:
        r = client.post("/api/v1/authorize", json={
            "principal_user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "cart_hash": "hash123",
            "amount_paise": 6_800_000,
            "category": "laptops",
            "merchant_id": str(uuid4()),
            "idempotency_key": f"idem-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["allowed"] is True
        assert data["failed_rule_id"] is None
        assert data["rule_count"] == 16

    def test_authorize_deny_principal_inactive(self, client) -> None:
        r = client.post("/api/v1/authorize", json={
            "principal_user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "cart_hash": "hash123",
            "amount_paise": 6_800_000,
            "category": "laptops",
            "merchant_id": str(uuid4()),
            "idempotency_key": f"idem-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
            "principal_active": False,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["allowed"] is False
        assert data["failed_rule_id"] == "AUTH_003_PRINCIPAL_ACTIVE"
        assert data["rule_count"] == 3  # Short-circuit

    def test_authorize_deny_nonce_reused(self, client) -> None:
        r = client.post("/api/v1/authorize", json={
            "principal_user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "cart_hash": "hash123",
            "amount_paise": 6_800_000,
            "category": "laptops",
            "merchant_id": str(uuid4()),
            "idempotency_key": f"idem-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
            "nonce_unused": False,
        })
        data = r.json()
        assert data["allowed"] is False
        assert data["failed_rule_id"] == "AUTH_015_NONCE_UNUSED"

    def test_get_decision(self, client) -> None:
        create = client.post("/api/v1/authorize", json={
            "principal_user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "cart_hash": "hash123",
            "amount_paise": 1_000_000,
            "category": "phones",
            "merchant_id": str(uuid4()),
            "idempotency_key": f"idem-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        })
        decision_id = create.json()["decision_id"]
        r = client.get(f"/api/v1/authorize/{decision_id}")
        assert r.status_code == 200
        assert r.json()["allowed"] is True


# ═══════════════════════════════════════════════════════
# Order & Payment API
# ═══════════════════════════════════════════════════════

class TestOrderAPI:

    def test_create_order(self, client) -> None:
        r = client.post("/api/v1/orders", json={
            "user_id": str(uuid4()),
            "cart_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "authorization_decision_id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "total_paise": 6_800_000,
            "cart_hash": "hash_abc",
            "idempotency_key": f"ord-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "created"
        assert data["total_paise"] == 6_800_000
        assert data["evidence_chain_length"] == 1

    def test_order_idempotency(self, client) -> None:
        idem_key = f"ord-{uuid4()}"
        payload = {
            "user_id": str(uuid4()),
            "cart_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "authorization_decision_id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "total_paise": 3_000_000,
            "cart_hash": "hash_xyz",
            "idempotency_key": idem_key,
            "authorization_nonce": f"nonce-{uuid4()}",
        }
        r1 = client.post("/api/v1/orders", json=payload)
        r2 = client.post("/api/v1/orders", json=payload)
        assert r1.json()["order_id"] == r2.json()["order_id"]  # Same order returned

    def test_initiate_payment(self, client) -> None:
        order = client.post("/api/v1/orders", json={
            "user_id": str(uuid4()),
            "cart_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "authorization_decision_id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "total_paise": 6_800_000,
            "cart_hash": "hash_pay",
            "idempotency_key": f"ord-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        })
        order_id = order.json()["order_id"]

        r = client.post(f"/api/v1/orders/{order_id}/payment", json={
            "amount_paise": 6_800_000,
            "idempotency_key": f"pay-{uuid4()}",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["local_state"] == "initiated"
        assert data["provider_confirmed_state"] is None
        assert data["is_paid"] is False

    def test_evidence_proof(self, client) -> None:
        order = client.post("/api/v1/orders", json={
            "user_id": str(uuid4()),
            "cart_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "authorization_decision_id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "total_paise": 6_800_000,
            "cart_hash": "hash_proof",
            "idempotency_key": f"ord-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        })
        order_id = order.json()["order_id"]

        # Add payment to grow evidence chain
        client.post(f"/api/v1/orders/{order_id}/payment", json={
            "amount_paise": 6_800_000,
            "idempotency_key": f"pay-{uuid4()}",
        })

        r = client.get(f"/api/v1/orders/{order_id}/proof")
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is True
        assert data["length"] == 2  # order.created + payment.initiated
        assert len(data["records"]) == 2


# ═══════════════════════════════════════════════════════
# MCP API
# ═══════════════════════════════════════════════════════

class TestMCPAPI:

    def test_list_all_tools(self, client) -> None:
        r = client.get("/api/v1/mcp/tools")
        assert r.status_code == 200
        assert r.json()["total"] == 8

    def test_list_buyer_tools(self, client) -> None:
        r = client.get("/api/v1/mcp/tools?capabilities=search,compare,negotiate,propose_cart,request_authorization,view_proof")
        assert r.status_code == 200
        assert r.json()["total"] == 6

    def test_list_merchant_tools(self, client) -> None:
        r = client.get("/api/v1/mcp/tools?capabilities=manage_catalog,approve_offer")
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_invoke_tool_allowed(self, client) -> None:
        r = client.post("/api/v1/mcp/tools/search_products/invoke", json={
            "agent_id": str(uuid4()),
            "agent_capabilities": ["search"],
            "parameters": {"query": "laptop"},
        })
        assert r.status_code == 200
        data = r.json()
        assert data["capability_check_passed"] is True
        assert data["result_status"] == "success"

    def test_invoke_tool_denied(self, client) -> None:
        r = client.post("/api/v1/mcp/tools/request_authorization/invoke", json={
            "agent_id": str(uuid4()),
            "agent_capabilities": ["search"],  # Missing request_authorization
            "parameters": {},
        })
        assert r.status_code == 200
        data = r.json()
        assert data["capability_check_passed"] is False
        assert data["result_status"] == "denied"

    def test_invoke_unknown_tool(self, client) -> None:
        r = client.post("/api/v1/mcp/tools/nonexistent_tool/invoke", json={
            "agent_id": str(uuid4()),
            "agent_capabilities": ["search"],
            "parameters": {},
        })
        data = r.json()
        assert data["capability_check_passed"] is False


# ═══════════════════════════════════════════════════════
# Validation
# ═══════════════════════════════════════════════════════

class TestValidation:

    def test_mandate_zero_amount_rejected(self, client) -> None:
        r = client.post("/api/v1/mandates", json={
            "user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_type": "daily",
            "max_amount_paise": 0,
        })
        assert r.status_code == 422

    def test_authorize_empty_cart_hash_rejected(self, client) -> None:
        r = client.post("/api/v1/authorize", json={
            "principal_user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "cart_hash": "",
            "amount_paise": 1_000_000,
            "category": "test",
            "merchant_id": str(uuid4()),
            "idempotency_key": "k",
            "authorization_nonce": "n",
        })
        assert r.status_code == 422

    def test_order_zero_total_rejected(self, client) -> None:
        r = client.post("/api/v1/orders", json={
            "user_id": str(uuid4()),
            "cart_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "authorization_decision_id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "total_paise": 0,
            "cart_hash": "hash",
            "idempotency_key": "k",
            "authorization_nonce": "n",
        })
        assert r.status_code == 422
