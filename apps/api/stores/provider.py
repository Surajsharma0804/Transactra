"""
Transactra — Store Provider (Dependency Injection)

Provides FastAPI dependencies for store access.
Auto-detects mode from DATABASE_URL environment variable:

- DATABASE_URL set + connectable → PostgresStore implementations
- Otherwise → MemoryStore implementations (demo mode)

Usage in routes:
    from apps.api.stores.provider import get_mandate_store, get_user_store
    
    @router.post("/mandates")
    async def create_mandate(
        mandate_store: MandateStore = Depends(get_mandate_store),
    ):
        ...
"""

from __future__ import annotations

import logging
from typing import Any

from apps.api.stores.base import (
    AgentStore,
    ConsentStore,
    MandateStore,
    OrderStore,
    UserStore,
)
from apps.api.stores.memory import (
    MemoryAgentStore,
    MemoryConsentStore,
    MemoryMandateStore,
    MemoryOrderStore,
    MemoryUserStore,
)

logger = logging.getLogger("transactra.stores")

# ── Singleton instances (shared across the application) ──

_mandate_store: MandateStore | None = None
_consent_store: ConsentStore | None = None
_order_store: OrderStore | None = None
_user_store: UserStore | None = None
_agent_store: AgentStore | None = None
_initialized = False


def _init_stores() -> None:
    """
    Initialize store singletons. Called once on first access.

    Checks if Postgres is available; falls back to in-memory.
    """
    global _mandate_store, _consent_store, _order_store
    global _user_store, _agent_store, _initialized

    if _initialized:
        return

    # Try Postgres first
    try:
        from backend.config import get_settings
        settings = get_settings()
        if settings.database_url and "postgresql" in settings.database_url:
            # TODO: Wire PostgresStore implementations when DB is running
            # For now, fall through to memory stores
            logger.info("DATABASE_URL configured but Postgres stores not yet wired — using memory stores")
    except Exception:
        pass

    # Default: in-memory stores
    _mandate_store = MemoryMandateStore()
    _consent_store = MemoryConsentStore()
    _order_store = MemoryOrderStore()
    _user_store = MemoryUserStore()
    _agent_store = MemoryAgentStore()
    _initialized = True
    logger.info("Store layer initialized (mode=memory)")


# ── FastAPI Dependencies ─────────────────────────────

def get_mandate_store() -> MandateStore:
    """FastAPI dependency for mandate store access."""
    _init_stores()
    assert _mandate_store is not None
    return _mandate_store


def get_consent_store() -> ConsentStore:
    """FastAPI dependency for consent store access."""
    _init_stores()
    assert _consent_store is not None
    return _consent_store


def get_order_store() -> OrderStore:
    """FastAPI dependency for order store access."""
    _init_stores()
    assert _order_store is not None
    return _order_store


def get_user_store() -> UserStore:
    """FastAPI dependency for user store access."""
    _init_stores()
    assert _user_store is not None
    return _user_store


def get_agent_store() -> AgentStore:
    """FastAPI dependency for agent store access."""
    _init_stores()
    assert _agent_store is not None
    return _agent_store


# ── Testing support ──────────────────────────────────

def reset_stores() -> None:
    """Reset all stores to fresh memory instances. For testing only."""
    global _mandate_store, _consent_store, _order_store
    global _user_store, _agent_store, _initialized
    _mandate_store = MemoryMandateStore()
    _consent_store = MemoryConsentStore()
    _order_store = MemoryOrderStore()
    _user_store = MemoryUserStore()
    _agent_store = MemoryAgentStore()
    _initialized = True
