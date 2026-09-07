"""
Transactra — Abstract Store Interfaces

Defines the contracts for mandate, consent, order, and user stores.
Implementations: MemoryStore (default), PostgresStore (opt-in via DATABASE_URL).

Using abstract base classes instead of runtime-protocol so violations
surface immediately at import, not at first call.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID


class MandateStore(ABC):
    """Abstract mandate persistence. O(1) per operation for in-memory."""

    @abstractmethod
    async def create(self, mandate_id: UUID, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def get(self, mandate_id: UUID) -> dict[str, Any] | None: ...

    @abstractmethod
    async def update(self, mandate_id: UUID, updates: dict[str, Any]) -> dict[str, Any] | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> list[dict[str, Any]]: ...


class ConsentStore(ABC):
    """Abstract consent persistence."""

    @abstractmethod
    async def create(self, consent_id: UUID, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def get(self, consent_id: UUID) -> dict[str, Any] | None: ...

    @abstractmethod
    async def update(self, consent_id: UUID, updates: dict[str, Any]) -> dict[str, Any] | None: ...


class OrderStore(ABC):
    """Abstract order persistence."""

    @abstractmethod
    async def create(self, order_id: UUID, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def get(self, order_id: UUID) -> dict[str, Any] | None: ...

    @abstractmethod
    async def update(self, order_id: UUID, updates: dict[str, Any]) -> dict[str, Any] | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> list[dict[str, Any]]: ...


class UserStore(ABC):
    """Abstract user persistence."""

    @abstractmethod
    async def create(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]: ...

    @abstractmethod
    async def get(self, user_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def update(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None: ...


class AgentStore(ABC):
    """Abstract agent persistence."""

    @abstractmethod
    async def get(self, agent_id: UUID) -> dict[str, Any] | None: ...

    @abstractmethod
    async def get_by_owner(self, owner_user_id: UUID) -> list[dict[str, Any]]: ...
