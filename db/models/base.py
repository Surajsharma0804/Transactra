"""
Transactra — SQLAlchemy 2.0 Declarative Base

All models inherit from this base. UUID primary keys, automatic timestamps.
No domain logic here — this is pure persistence infrastructure.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, MetaData, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry

# Naming convention for constraints — enables deterministic migration names
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Base class for all Transactra ORM models.

    Provides:
    - UUID primary key (gen_random_uuid server-side)
    - created_at / updated_at timestamps with timezone
    - Consistent naming convention for all constraints
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map = {
        uuid.UUID: PG_UUID(as_uuid=True),
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin for created_at / updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UUIDPrimaryKeyMixin:
    """Mixin for UUID primary key with server-side generation."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
