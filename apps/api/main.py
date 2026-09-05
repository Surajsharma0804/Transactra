"""
Transactra — FastAPI Application

Entry point for the API server. Provides:
- Health check endpoint
- CORS middleware
- Correlation ID middleware (X-Correlation-ID)
- Structured error handling
- Lifespan management (DB pool)
"""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel

from backend.config import get_settings
from db.session import get_engine

logger = logging.getLogger("transactra.api")


# ── Lifespan ─────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: DB engine startup/shutdown."""
    settings = get_settings()
    logger.info(
        "Transactra API starting",
        extra={"env": settings.app_env, "version": settings.app_version},
    )
    engine = get_engine()
    yield
    await engine.dispose()
    logger.info("Transactra API shutdown complete")


# ── Application ──────────────────────────────────────

app = FastAPI(
    title="Transactra",
    description="The Trust Infrastructure for Agentic Commerce",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

# ── Register Routers ─────────────────────────────────
from apps.api.routes.catalog import router as catalog_router
from apps.api.routes.mandates import router as mandates_router
from apps.api.routes.authorization import router as authorization_router
from apps.api.routes.orders import router as orders_router
from apps.api.routes.mcp import router as mcp_router

app.include_router(catalog_router, prefix="/api/v1")
app.include_router(mandates_router, prefix="/api/v1")
app.include_router(authorization_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")

# ── CORS ─────────────────────────────────────────────

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)


# ── Correlation ID Middleware ────────────────────────

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next) -> Response:
    """
    Attach a correlation ID to every request for end-to-end tracing.

    If X-Correlation-ID header is present, use it.
    Otherwise, generate a new UUID4.

    Complexity: O(1).
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# ── Request Timing Middleware ────────────────────────

@app.middleware("http")
async def timing_middleware(request: Request, call_next) -> Response:
    """Record request processing time in response headers. O(1)."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    return response


# ── Response Models ──────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    timestamp: str


class ApiErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: dict[str, Any]
    correlation_id: str
    timestamp: str


# ── Health Check ─────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
)
async def health_check() -> HealthResponse:
    """
    System health check. Returns 200 if API is operational.
    Used by Docker HEALTHCHECK and load balancers.

    Complexity: O(1) — no DB call, no computation.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc).isoformat() + "Z",
    )


# ── API Info ─────────────────────────────────────────

@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """API root — returns basic info."""
    return {
        "name": "Transactra",
        "description": "The Trust Infrastructure for Agentic Commerce",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


# ── Global Exception Handler ────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """
    Catch-all exception handler. Fail closed — never expose internals.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.exception(
        "Unhandled exception",
        extra={"correlation_id": correlation_id},
    )
    return ORJSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
            },
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        },
    )
