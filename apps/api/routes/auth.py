"""
Transactra — Authentication API Routes

Endpoints:
- POST /auth/register — Register a new user
- POST /auth/login    — Login and get JWT token
- POST /auth/refresh  — Refresh an expiring token
- POST /auth/logout   — Logout (clear cookie)

Uses in-memory store for demo. Production would use DB.
Passwords hashed with bcrypt via passlib.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator

from apps.api.security import (
    CurrentUser,
    TokenResponse,
    create_access_token,
    generate_csrf_token,
    get_current_user,
    set_csrf_cookie,
)
from backend.config import get_settings

logger = logging.getLogger("transactra.auth")

router = APIRouter(prefix="/auth", tags=["authentication"])

# ── Password hashing — bcrypt, O(1) per hash ────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── In-memory user store (production → DB) ───────────
# Map<user_id_str, { id, name, email, password_hash, role, created_at }>
_users: dict[str, dict] = {}
# Map<email, user_id> for O(1) email lookup
_email_index: dict[str, str] = {}


# ── Request/Response Models ──────────────────────────

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(pattern="^(buyer|merchant)$")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Strip HTML tags from name — O(n)."""
        import re
        return re.sub(r"<[^>]*>", "", v).strip()


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=128)


class RegisterResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    message: str


# ── Endpoints ────────────────────────────────────────

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(req: RegisterRequest, response: Response) -> RegisterResponse:
    """
    Register a new user account.

    - Email must be unique
    - Password hashed with bcrypt (cost factor 12)
    - Returns user details (no token — must login separately)

    Complexity: O(1) for lookup, O(n) for bcrypt where n = cost factor.
    """
    # Check duplicate email — O(1) via index
    if req.email in _email_index:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid4())
    now = datetime.now(timezone.utc)

    # Hash password — bcrypt O(n) with cost factor
    password_hash = _pwd_context.hash(req.password)

    user = {
        "id": user_id,
        "name": req.name,
        "email": req.email,
        "password_hash": password_hash,
        "role": req.role,
        "created_at": now.isoformat() + "Z",
    }

    _users[user_id] = user
    _email_index[req.email] = user_id

    # Set CSRF cookie for subsequent requests
    csrf = generate_csrf_token()
    set_csrf_cookie(response, csrf)

    logger.info("User registered", extra={"user_id": user_id, "role": req.role})

    return RegisterResponse(
        user_id=user_id,
        name=req.name,
        email=req.email,
        role=req.role,
        message="Account created. Please login.",
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, response: Response) -> TokenResponse:
    """
    Authenticate user and return JWT token.

    - Validates credentials against stored bcrypt hash
    - Returns JWT access token
    - Sets HttpOnly cookie with token (for browser requests)
    - Sets CSRF cookie

    Complexity: O(1) lookup + O(n) bcrypt verify.
    """
    # Lookup by email — O(1)
    user_id = _email_index.get(req.email.strip().lower())
    if not user_id:
        # Constant-time response to prevent user enumeration
        _pwd_context.hash("dummy")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = _users[user_id]

    # Verify password — O(n) bcrypt
    if not _pwd_context.verify(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    settings = get_settings()
    expires_seconds = settings.jwt_expiry_minutes * 60

    # Create JWT — O(1)
    token = create_access_token(
        user_id=user["id"],
        role=user["role"],
        name=user["name"],
    )

    # Set secure cookie — O(1)
    response.set_cookie(
        key="transactra_token",
        value=token,
        httponly=True,
        samesite="strict",
        secure=settings.app_env == "production",
        max_age=expires_seconds,
        path="/",
    )

    # Set CSRF cookie
    csrf = generate_csrf_token()
    set_csrf_cookie(response, csrf)

    logger.info("User logged in", extra={"user_id": user["id"]})

    return TokenResponse(
        access_token=token,
        expires_in=expires_seconds,
        user_id=user["id"],
        role=user["role"],
        name=user["name"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
) -> TokenResponse:
    """
    Refresh an expiring token.

    Requires a valid (not yet expired) current token.
    Returns a new token with fresh expiry.

    Complexity: O(1).
    """
    user = _users.get(current_user.id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    settings = get_settings()
    expires_seconds = settings.jwt_expiry_minutes * 60

    token = create_access_token(
        user_id=user["id"],
        role=user["role"],
        name=user["name"],
    )

    response.set_cookie(
        key="transactra_token",
        value=token,
        httponly=True,
        samesite="strict",
        secure=settings.app_env == "production",
        max_age=expires_seconds,
        path="/",
    )

    return TokenResponse(
        access_token=token,
        expires_in=expires_seconds,
        user_id=user["id"],
        role=user["role"],
        name=user["name"],
    )


@router.post("/logout", status_code=200)
async def logout(response: Response) -> dict[str, str]:
    """
    Logout — clear authentication cookies.

    Complexity: O(1).
    """
    response.delete_cookie("transactra_token", path="/")
    response.delete_cookie("csrf_token", path="/")
    return {"status": "logged_out", "message": "Cookies cleared"}
