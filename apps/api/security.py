"""
Transactra — Security Module

Provides:
- JWT token creation and validation
- CSRF double-submit cookie protection
- FastAPI dependencies for route protection

All operations are O(1) except token validation which is O(n) on payload size.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.config import get_settings

logger = logging.getLogger("transactra.security")

# ── Bearer token extractor (optional — allows both header and cookie) ──
_bearer_scheme = HTTPBearer(auto_error=False)


# ── Token Models ─────────────────────────────────────

class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: str          # user_id
    role: str         # 'buyer' | 'merchant'
    name: str
    exp: int          # expiry timestamp
    iat: int          # issued-at timestamp
    jti: str          # unique token ID (for revocation)


class TokenResponse(BaseModel):
    """Token pair returned on login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int   # seconds
    user_id: str
    role: str
    name: str


class CurrentUser(BaseModel):
    """Authenticated user extracted from JWT."""
    id: str
    role: str
    name: str
    token_id: str


# ── JWT Token Operations — O(1) ──────────────────────

def create_access_token(
    user_id: str,
    role: str,
    name: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Complexity: O(1) — HMAC-SHA256 signing.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.jwt_expiry_minutes))

    payload = {
        "sub": user_id,
        "role": role,
        "name": name,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": secrets.token_hex(16),  # unique token ID
        "iss": "transactra",
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Raises HTTPException on invalid/expired token.
    Complexity: O(1) — HMAC-SHA256 verification.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer="transactra",
            options={"require": ["sub", "role", "name", "exp", "iat", "jti"]},
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


# ── FastAPI Dependencies ─────────────────────────────

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    Extract and validate the current user from JWT.

    Checks in order:
    1. Authorization: Bearer <token> header
    2. transactra_token cookie (fallback for browser requests)

    Complexity: O(1).
    """
    token: str | None = None

    # 1. Try Authorization header
    if credentials and credentials.credentials:
        token = credentials.credentials

    # 2. Fallback to cookie
    if not token:
        token = request.cookies.get("transactra_token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    return CurrentUser(
        id=payload.sub,
        role=payload.role,
        name=payload.name,
        token_id=payload.jti,
    )


def require_role(required_role: str):
    """
    Dependency factory — enforces a specific role.

    Usage: `current_user: CurrentUser = Depends(require_role("buyer"))`

    Complexity: O(1).
    """
    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"This action requires '{required_role}' role",
            )
        return user
    return _check


# ── CSRF Protection — Double Submit Cookie ───────────

def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token. O(1)."""
    return secrets.token_hex(32)


def set_csrf_cookie(response: Response, token: str) -> None:
    """Set CSRF token as a cookie. O(1)."""
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,   # JS needs to read this to send in header
        samesite="strict",
        secure=get_settings().app_env == "production",
        max_age=3600,
        path="/",
    )


def validate_csrf(request: Request) -> None:
    """
    Validate CSRF double-submit: cookie must match X-CSRF-Token header.

    Skips validation for:
    - GET/HEAD/OPTIONS requests (safe methods)
    - Webhook endpoints (server-to-server)

    Complexity: O(1) — constant-time comparison.
    """
    safe_methods = {"GET", "HEAD", "OPTIONS"}
    if request.method in safe_methods:
        return

    # Skip for webhook endpoints
    if "/webhook" in request.url.path:
        return

    # Skip for auth endpoints (login/register don't have CSRF yet)
    if "/auth/" in request.url.path:
        return

    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or not header_token:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    # Constant-time comparison to prevent timing attacks — O(1)
    if not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=403, detail="CSRF token mismatch")


# ── Security Headers ─────────────────────────────────

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(self), geolocation=()",
    "Cache-Control": "no-store, no-cache, must-revalidate",
}


def get_hsts_header(settings) -> dict[str, str]:
    """Get HSTS header for production. O(1)."""
    if settings.app_env == "production":
        return {"Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload"}
    return {}
""", "toolAction": "Creating security module", "toolSummary": "Security module"}
