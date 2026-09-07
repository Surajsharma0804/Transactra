"""
Transactra — In-Memory Store Implementations

Thread-safe dict-backed stores extracted from the route modules.
Used as default when no DATABASE_URL is configured.

These are the same dicts that were previously inlined in the route files,
now behind the abstract interface so they can be swapped for Postgres.

Concurrency note: Python's GIL makes single dict operations atomic,
but production should use Postgres with proper row-level locking.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from apps.api.stores.base import (
    AgentStore,
    ConsentStore,
    MandateStore,
    OrderStore,
    UserStore,
)


class MemoryMandateStore(MandateStore):
    """In-memory mandate store. O(1) per operation."""

    def __init__(self) -> None:
        self._data: dict[UUID, dict[str, Any]] = {}

    async def create(self, mandate_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        self._data[mandate_id] = data
        return data

    async def get(self, mandate_id: UUID) -> dict[str, Any] | None:
        return self._data.get(mandate_id)

    async def update(self, mandate_id: UUID, updates: dict[str, Any]) -> dict[str, Any] | None:
        record = self._data.get(mandate_id)
        if record is None:
            return None
        record.update(updates)
        return record

    async def list_by_user(self, user_id: UUID) -> list[dict[str, Any]]:
        return [m for m in self._data.values() if m.get("user_id") == user_id]


class MemoryConsentStore(ConsentStore):
    """In-memory consent store. O(1) per operation."""

    def __init__(self) -> None:
        self._data: dict[UUID, dict[str, Any]] = {}

    async def create(self, consent_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        self._data[consent_id] = data
        return data

    async def get(self, consent_id: UUID) -> dict[str, Any] | None:
        return self._data.get(consent_id)

    async def update(self, consent_id: UUID, updates: dict[str, Any]) -> dict[str, Any] | None:
        record = self._data.get(consent_id)
        if record is None:
            return None
        record.update(updates)
        return record


class MemoryOrderStore(OrderStore):
    """In-memory order store. O(1) per operation, O(n) for list."""

    def __init__(self) -> None:
        self._data: dict[UUID, dict[str, Any]] = {}

    async def create(self, order_id: UUID, data: dict[str, Any]) -> dict[str, Any]:
        self._data[order_id] = data
        return data

    async def get(self, order_id: UUID) -> dict[str, Any] | None:
        return self._data.get(order_id)

    async def update(self, order_id: UUID, updates: dict[str, Any]) -> dict[str, Any] | None:
        record = self._data.get(order_id)
        if record is None:
            return None
        record.update(updates)
        return record

    async def list_by_user(self, user_id: UUID) -> list[dict[str, Any]]:
        return [o for o in self._data.values() if o.get("user_id") == user_id]


class MemoryUserStore(UserStore):
    """In-memory user store with email index. O(1) per operation."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._email_index: dict[str, str] = {}

    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        self._data[user_id] = data
        email = data.get("email")
        if email:
            self._email_index[email] = user_id
        return data

    async def get(self, user_id: str) -> dict[str, Any] | None:
        return self._data.get(user_id)

    async def get_by_email(self, email: str) -> dict[str, Any] | None:
        user_id = self._email_index.get(email)
        if user_id is None:
            return None
        return self._data.get(user_id)

    async def update(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        record = self._data.get(user_id)
        if record is None:
            return None
        record.update(updates)
        return record


class MemoryAgentStore(AgentStore):
    """In-memory agent store. O(1) per operation."""

    def __init__(self) -> None:
        self._data: dict[UUID, dict[str, Any]] = {}

    async def get(self, agent_id: UUID) -> dict[str, Any] | None:
        return self._data.get(agent_id)

    async def get_by_owner(self, owner_user_id: UUID) -> list[dict[str, Any]]:
        return [a for a in self._data.values() if a.get("owner_user_id") == owner_user_id]
