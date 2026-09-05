"""
Transactra — Application Configuration

Single source of truth for all configuration. Loaded from environment variables.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────
    app_env: str = "development"
    app_name: str = "Transactra"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    api_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"

    # ── Database ─────────────────────────────────────
    database_url: str = "postgresql+asyncpg://transactra:transactra@db:5432/transactra"
    database_url_sync: str = "postgresql+psycopg://transactra:transactra@db:5432/transactra"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # ── Redis ────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"

    # ── LLM ──────────────────────────────────────────
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_primary_model: str = "gpt-4o"
    llm_fallback_model: str = "gpt-4o-mini"
    llm_call_timeout: int = 30
    llm_max_retries: int = 2

    # ── Razorpay ─────────────────────────────────────
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # ── Security ─────────────────────────────────────
    cors_origins: str = "http://localhost:3000"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    mandate_signing_secret: str = ""

    # ── Operational ──────────────────────────────────
    reconciliation_interval_seconds: int = 300
    payment_timeout_seconds: int = 900
    idempotency_ttl_days: int = 90

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings (cached singleton). O(1) after first call."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
