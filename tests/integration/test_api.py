"""
Transactra — API Integration Tests

Tests the full HTTP API flow with proper authentication:
- Health check
- User registration & login
- Mandate creation → Consent → Authorization → Order → Payment → Proof
- MCP tool listing and invocation with capability checks
- Error handling (404, 409, validation)

Uses FastAPI TestClient (no actual server needed).
Stores are reset between test classes to ensure isolation.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.stores.provider import reset_stores


@pytest.fixture(autouse=True)
def _reset():
    """Reset in-memory stores before each test to ensure isolation."""
    reset_stores()
    yield
    reset_stores()


@pytest.fixture
def client():
    return TestClient(app)


def _register_and_login(client, role="buyer") -> tuple[str, str, str]:
    """
    Register a user and login, returning (token, user_id, email).

    Helper to avoid duplicating auth setup in every test.
    """
    email = f"test_{uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"
    name = "Test User"

    # Register
    reg = client.post("/api/v1/auth/register", json={
        "name": name,
        "email": email,
        "password": password,
        "role": role,
    })
    assert reg.status_code == 201, f"Registration failed: {reg.json()}"

    # Login
    login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    assert login.status_code == 200, f"Login failed: {login.json()}"
    data = login.json()
    return data["access_token"], data["user_id"], email


def _auth_headers(token: str) -> dict[str, str]:
    """Build authorization headers from a JWT token."""
    return {"Authorization": f"Bearer {token}"}


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
# Auth API
# ═══════════════════════════════════════════════════════

class TestAuthAPI:

    def test_register(self, client) -> None:
        r = client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "auth_test@example.com",
            "password": "SecurePass123!",
            "role": "buyer",
        })
        assert r.status_code == 201
        assert r.json()["email"] == "auth_test@example.com"

    def test_register_duplicate_email(self, client) -> None:
        payload = {
            "name": "Test", "email": "dup@example.com",
            "password": "SecurePass123!", "role": "buyer",
        }
        client.post("/api/v1/auth/register", json=payload)
        r = client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 409

    def test_login(self, client) -> None:
        token, user_id, email = _register_and_login(client)
        assert token
        assert user_id

    def test_login_wrong_password(self, client) -> None:
        email = f"wrong_{uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={
            "name": "Test", "email": email,
            "password": "RealPass123!", "role": "buyer",
        })
        r = client.post("/api/v1/auth/login", json={
            "email": email, "password": "WrongPass123!",
        })
        assert r.status_code == 401


# ═══════════════════════════════════════════════════════
# Mandate API (authenticated)
# ═══════════════════════════════════════════════════════

class TestMandateAPI:

    def test_create_mandate(self, client) -> None:
        token, user_id, _ = _register_and_login(client)
        r = client.post("/api/v1/mandates", json={
            "user_id": user_id,
            "agent_id": str(uuid4()),
            "mandate_type": "per_transaction",
            "max_amount_paise": 10_000_000,
        }, headers=_auth_headers(token))
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "active"
        assert data["max_amount_paise"] == 10_000_000
        assert data["remaining_paise"] == 10_000_000

    def test_get_mandate(self, client) -> None:
        token, user_id, _ = _register_and_login(client)
        create = client.post("/api/v1/mandates", json={
            "user_id": user_id,
            "agent_id": str(uuid4()),
            "mandate_type": "daily",
            "max_amount_paise": 5_000_000,
        }, headers=_auth_headers(token))
        mandate_id = create.json()["mandate_id"]
        r = client.get(f"/api/v1/mandates/{mandate_id}", headers=_auth_headers(token))
        assert r.status_code == 200
        assert r.json()["max_amount_paise"] == 5_000_000

    def test_mandate_not_found(self, client) -> None:
        token, _, _ = _register_and_login(client)
        r = client.get(f"/api/v1/mandates/{uuid4()}", headers=_auth_headers(token))
        assert r.status_code == 404

    def test_mandate_requires_auth(self, client) -> None:
        r = client.post("/api/v1/mandates", json={
            "user_id": str(uuid4()),
            "agent_id": str(uuid4()),
            "mandate_type": "per_transaction",
            "max_amount_paise": 10_000_000,
        })
        assert r.status_code == 401

    def test_create_consent(self, client) -> None:
        token, user_id, _ = _register_and_login(client)
        mandate = client.post("/api/v1/mandates", json={
            "user_id": user_id,
            "agent_id": str(uuid4()),
            "mandate_type": "per_transaction",
            "max_amount_paise": 10_000_000,
        }, headers=_auth_headers(token))
        mandate_id = mandate.json()["mandate_id"]

        r = client.post(f"/api/v1/mandates/{mandate_id}/consent", json={
            "user_id": user_id,
            "cart_hash": "abc123def456",
            "amount_paise": 6_800_000,
        }, headers=_auth_headers(token))
        assert r.status_code == 201
        assert r.json()["status"] == "approved"
        assert r.json()["cart_hash"] == "abc123def456"

    def test_consent_exceeds_budget(self, client) -> None:
        token, user_id, _ = _register_and_login(client)
        mandate = client.post("/api/v1/mandates", json={
            "user_id": user_id,
            "agent_id": str(uuid4()),
            "mandate_type": "per_transaction",
            "max_amount_paise": 1_000_000,
        }, headers=_auth_headers(token))
        mandate_id = mandate.json()["mandate_id"]

        r = client.post(f"/api/v1/mandates/{mandate_id}/consent", json={
            "user_id": user_id,
            "cart_hash": "abc",
            "amount_paise": 5_000_000,
        }, headers=_auth_headers(token))
        assert r.status_code == 409


# ═══════════════════════════════════════════════════════
# Authorization API (full flow: register → mandate → consent → authorize)
# ═══════════════════════════════════════════════════════

class TestAuthorizationAPI:

    def _setup_full_flow(self, client):
        """Create user, mandate, consent — returns everything needed to authorize."""
        token, user_id, _ = _register_and_login(client)
        agent_id = str(uuid4())
        merchant_id = str(uuid4())

        # Create mandate
        mandate = client.post("/api/v1/mandates", json={
            "user_id": user_id,
            "agent_id": agent_id,
            "mandate_type": "per_transaction",
            "max_amount_paise": 10_000_000,
        }, headers=_auth_headers(token))
        mandate_id = mandate.json()["mandate_id"]

        # Create consent
        cart_hash = f"cart_{uuid4().hex[:8]}"
        consent = client.post(f"/api/v1/mandates/{mandate_id}/consent", json={
            "user_id": user_id,
            "cart_hash": cart_hash,
            "amount_paise": 6_800_000,
        }, headers=_auth_headers(token))
        consent_id = consent.json()["consent_id"]

        return {
            "token": token,
            "user_id": user_id,
            "agent_id": agent_id,
            "mandate_id": mandate_id,
            "consent_id": consent_id,
            "cart_hash": cart_hash,
            "merchant_id": merchant_id,
        }

    def test_authorize_allow(self, client) -> None:
        ctx = self._setup_full_flow(client)
        r = client.post("/api/v1/authorize", json={
            "principal_user_id": ctx["user_id"],
            "agent_id": ctx["agent_id"],
            "mandate_id": ctx["mandate_id"],
            "consent_id": ctx["consent_id"],
            "cart_hash": ctx["cart_hash"],
            "amount_paise": 6_800_000,
            "category": "laptops",
            "merchant_id": ctx["merchant_id"],
            "idempotency_key": f"idem-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        }, headers=_auth_headers(ctx["token"]))
        assert r.status_code == 200
        data = r.json()
        assert data["allowed"] is True
        assert data["failed_rule_id"] is None
        assert data["rule_count"] == 16

    def test_authorize_deny_no_mandate(self, client) -> None:
        """Authorization fails when mandate doesn't exist."""
        token, user_id, _ = _register_and_login(client)
        r = client.post("/api/v1/authorize", json={
            "principal_user_id": user_id,
            "agent_id": str(uuid4()),
            "mandate_id": str(uuid4()),  # Non-existent
            "consent_id": str(uuid4()),
            "cart_hash": "hash123",
            "amount_paise": 6_800_000,
            "category": "laptops",
            "merchant_id": str(uuid4()),
            "idempotency_key": f"idem-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        }, headers=_auth_headers(token))
        assert r.status_code == 200
        data = r.json()
        assert data["allowed"] is False
        # Should fail on mandate existence check
        assert "MANDATE" in data["failed_rule_id"]

    def test_get_decision(self, client) -> None:
        ctx = self._setup_full_flow(client)
        create = client.post("/api/v1/authorize", json={
            "principal_user_id": ctx["user_id"],
            "agent_id": ctx["agent_id"],
            "mandate_id": ctx["mandate_id"],
            "consent_id": ctx["consent_id"],
            "cart_hash": ctx["cart_hash"],
            "amount_paise": 1_000_000,
            "category": "phones",
            "merchant_id": ctx["merchant_id"],
            "idempotency_key": f"idem-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        }, headers=_auth_headers(ctx["token"]))
        decision_id = create.json()["decision_id"]
        r = client.get(f"/api/v1/authorize/{decision_id}")
        assert r.status_code == 200
        assert r.json()["allowed"] is True


# ═══════════════════════════════════════════════════════
# Order & Payment API
# ═══════════════════════════════════════════════════════

class TestOrderAPI:

    def _create_order(self, client) -> tuple[str, str, dict]:
        """Helper: register, login, create order. Returns (token, order_id, user_id)."""
        token, user_id, _ = _register_and_login(client)
        r = client.post("/api/v1/orders", json={
            "user_id": user_id,
            "cart_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "authorization_decision_id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "total_paise": 6_800_000,
            "cart_hash": "hash_abc",
            "idempotency_key": f"ord-{uuid4()}",
            "authorization_nonce": f"nonce-{uuid4()}",
        }, headers=_auth_headers(token))
        assert r.status_code == 201
        return token, r.json()["order_id"], {"user_id": user_id}

    def test_create_order(self, client) -> None:
        token, order_id, _ = self._create_order(client)
        assert order_id

    def test_get_order(self, client) -> None:
        token, order_id, _ = self._create_order(client)
        r = client.get(f"/api/v1/orders/{order_id}", headers=_auth_headers(token))
        assert r.status_code == 200
        assert r.json()["status"] == "created"

    def test_order_requires_auth(self, client) -> None:
        r = client.post("/api/v1/orders", json={
            "user_id": str(uuid4()),
            "cart_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "authorization_decision_id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "total_paise": 6_800_000,
            "cart_hash": "h",
            "idempotency_key": "k",
            "authorization_nonce": "n",
        })
        assert r.status_code == 401

    def test_initiate_payment(self, client) -> None:
        token, order_id, _ = self._create_order(client)
        r = client.post(f"/api/v1/orders/{order_id}/payment", json={
            "amount_paise": 6_800_000,
            "idempotency_key": f"pay-{uuid4()}",
        }, headers=_auth_headers(token))
        assert r.status_code == 201
        data = r.json()
        assert data["local_state"] == "initiated"
        assert data["provider_confirmed_state"] is None
        assert data["is_paid"] is False

    def test_evidence_proof(self, client) -> None:
        token, order_id, _ = self._create_order(client)
        # Add payment to grow evidence chain
        client.post(f"/api/v1/orders/{order_id}/payment", json={
            "amount_paise": 6_800_000,
            "idempotency_key": f"pay-{uuid4()}",
        }, headers=_auth_headers(token))

        r = client.get(f"/api/v1/orders/{order_id}/proof", headers=_auth_headers(token))
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
        token, user_id, _ = _register_and_login(client)
        r = client.post("/api/v1/mandates", json={
            "user_id": user_id,
            "agent_id": str(uuid4()),
            "mandate_type": "daily",
            "max_amount_paise": 0,
        }, headers=_auth_headers(token))
        assert r.status_code == 422

    def test_authorize_empty_cart_hash_rejected(self, client) -> None:
        token, user_id, _ = _register_and_login(client)
        r = client.post("/api/v1/authorize", json={
            "principal_user_id": user_id,
            "agent_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "cart_hash": "",
            "amount_paise": 1_000_000,
            "category": "test",
            "merchant_id": str(uuid4()),
            "idempotency_key": "k",
            "authorization_nonce": "n",
        }, headers=_auth_headers(token))
        assert r.status_code == 422

    def test_order_zero_total_rejected(self, client) -> None:
        token, user_id, _ = _register_and_login(client)
        r = client.post("/api/v1/orders", json={
            "user_id": user_id,
            "cart_id": str(uuid4()),
            "mandate_id": str(uuid4()),
            "consent_id": str(uuid4()),
            "authorization_decision_id": str(uuid4()),
            "merchant_id": str(uuid4()),
            "total_paise": 0,
            "cart_hash": "hash",
            "idempotency_key": "k",
            "authorization_nonce": "n",
        }, headers=_auth_headers(token))
        assert r.status_code == 422
