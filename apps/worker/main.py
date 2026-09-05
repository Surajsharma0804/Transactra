"""
Transactra — Background Worker

Handles:
- Outbox event publishing (transactional outbox pattern)
- Reconciliation sweeps (stuck payments)
- Expired mandate/consent cleanup
- Trust evidence computation

Runs as a separate process alongside the API.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone, timedelta

from backend.config import get_settings

logger = logging.getLogger("transactra.worker")

# Graceful shutdown flag
_shutdown = asyncio.Event()


async def outbox_processor() -> None:
    """
    Process outbox events (transactional outbox pattern).

    Scans the in-memory order/payment stores for events that
    haven't been published yet and marks them as processed.

    In production with PostgreSQL, this uses:
    SELECT FOR UPDATE SKIP LOCKED for worker concurrency.

    Interval: 1 second.
    Complexity: O(n) per sweep where n = pending events.
    """
    settings = get_settings()
    while not _shutdown.is_set():
        try:
            # Import the in-memory stores from routes
            from apps.api.routes.orders import _orders, _payments, _evidence_chains

            published_count = 0
            for order_id, order in _orders.items():
                # Check for orders with unpublished evidence
                chain = _evidence_chains.get(order_id)
                if chain and not order.get("events_published"):
                    # Mark events as published (in production, this would
                    # publish to a message queue like Redis/Kafka)
                    order["events_published"] = True
                    published_count += 1

            if published_count > 0:
                logger.info(f"Outbox: published events for {published_count} orders")

            await asyncio.sleep(1)
        except Exception:
            logger.exception("Outbox processor error")
            await asyncio.sleep(5)


async def reconciliation_sweep() -> None:
    """
    Find stuck payments and reconcile with provider.

    A payment is "stuck" if:
    - local_state == "initiated"
    - created_at > payment_timeout_seconds ago
    - provider_confirmed_state is still None (no webhook received)

    For stuck payments, marks them as needing manual reconciliation.
    In production with Razorpay keys configured, would poll Razorpay's
    GET /v1/payments/:id endpoint to get the real status.

    Interval: reconciliation_interval_seconds (default 300s = 5 min).
    Complexity: O(p) per sweep where p = payments count.
    """
    settings = get_settings()
    while not _shutdown.is_set():
        try:
            from apps.api.routes.orders import _payments

            now = datetime.now(timezone.utc)
            timeout = timedelta(seconds=settings.payment_timeout_seconds)
            reconciled_count = 0

            for payment_id, payment in _payments.items():
                if (
                    payment["local_state"] == "initiated"
                    and payment["provider_confirmed_state"] is None
                    and not payment.get("needs_reconciliation")
                ):
                    # Parse created_at timestamp
                    created_str = payment.get("created_at", "")
                    if isinstance(created_str, str) and created_str:
                        try:
                            created = datetime.fromisoformat(
                                created_str.replace("Z", "+00:00")
                            )
                            if now - created > timeout:
                                payment["needs_reconciliation"] = True
                                payment["local_state"] = "timeout"
                                reconciled_count += 1
                                logger.warning(
                                    f"Payment {payment_id} timed out after "
                                    f"{settings.payment_timeout_seconds}s — "
                                    f"flagged for reconciliation"
                                )
                        except ValueError:
                            pass

            if reconciled_count > 0:
                logger.info(
                    f"Reconciliation: flagged {reconciled_count} stuck payments"
                )

            await asyncio.sleep(settings.reconciliation_interval_seconds)
        except Exception:
            logger.exception("Reconciliation sweep error")
            await asyncio.sleep(60)


async def expiry_cleanup() -> None:
    """
    Clean up expired mandates and consents.

    Scans all active mandates and consents, checking valid_until / expires_at.
    Expired items get status set to "expired".

    Runs every 60 seconds.
    Complexity: O(m + c) where m = mandates, c = consents.
    """
    while not _shutdown.is_set():
        try:
            from apps.api.routes.mandates import _mandates, _consents

            now = datetime.now(timezone.utc)
            expired_mandates = 0
            expired_consents = 0

            # Expire mandates past their valid_until
            for mandate_id, mandate in _mandates.items():
                if mandate["status"] == "active" and mandate.get("valid_until"):
                    valid_until = mandate["valid_until"]
                    if isinstance(valid_until, datetime) and now > valid_until:
                        mandate["status"] = "expired"
                        expired_mandates += 1
                        logger.info(f"Mandate {mandate_id} expired")

            # Expire consents past their expires_at
            for consent_id, consent in _consents.items():
                if consent["status"] == "approved" and consent.get("expires_at"):
                    expires_at = consent["expires_at"]
                    if isinstance(expires_at, datetime) and now > expires_at:
                        consent["status"] = "expired"
                        expired_consents += 1
                        logger.info(f"Consent {consent_id} expired")

            if expired_mandates or expired_consents:
                logger.info(
                    f"Expiry cleanup: {expired_mandates} mandates, "
                    f"{expired_consents} consents expired"
                )

            await asyncio.sleep(60)
        except Exception:
            logger.exception("Expiry cleanup error")
            await asyncio.sleep(60)


async def main() -> None:
    """Start all worker tasks."""
    settings = get_settings()
    logger.info(
        "Transactra Worker starting",
        extra={"env": settings.app_env},
    )

    # Register signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: _shutdown.set())
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    # Run all worker tasks concurrently
    tasks = [
        asyncio.create_task(outbox_processor(), name="outbox"),
        asyncio.create_task(reconciliation_sweep(), name="reconciliation"),
        asyncio.create_task(expiry_cleanup(), name="expiry"),
    ]

    logger.info("Worker tasks started: outbox, reconciliation, expiry")

    # Wait for shutdown signal
    await _shutdown.wait()

    logger.info("Shutdown signal received, stopping tasks...")
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Worker shutdown complete")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
