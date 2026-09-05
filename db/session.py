"""
Transactra — Async Database Session Factory

Provides async SQLAlchemy sessions for the API layer.
Connection pooling configured for optimal throughput.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import get_settings


def _create_engine():
    """
    Create async engine with connection pooling.

    Pool strategy:
    - pool_size: steady-state connections (20 default)
    - max_overflow: burst capacity above pool_size (10 default)
    - pool_timeout: max wait for connection from pool (30s)
    - pool_pre_ping: verify connections before use (handles DB restarts)

    Total max connections = pool_size + max_overflow = 30 default.
    """
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_pre_ping=True,
        echo=settings.app_env == "development",
    )


_engine = None
_session_factory = None


def get_engine():
    """Get or create the async engine (lazy singleton)."""
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the session factory (lazy singleton)."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async DB sessions.

    Usage:
        @app.get("/example")
        async def example(session: AsyncSession = Depends(get_session)):
            ...

    Session is committed on success, rolled back on exception.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
