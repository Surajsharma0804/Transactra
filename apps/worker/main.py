"""
Transactra — Background Worker

Handles:
- Outbox event publishing
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

from backend.config import get_settings

logger = logging.getLogger("transactra.worker")

# Graceful shutdown flag
_shutdown = asyncio.Event()


async def outbox_processor() -> None:
    """
    Process outbox events (transactional outbox pattern).
    Polls pending events and publishes them.

    Uses SELECT FOR UPDATE SKIP LOCKED for worker concurrency.
    Interval: 1 second.
    """
    settings = get_settings()
    while not _shutdown.is_set():
        try:
            # TODO: Phase 9 — implement outbox event processing
            await asyncio.sleep(1)
        except Exception:
            logger.exception("Outbox processor error")
            await asyncio.sleep(5)


async def reconciliation_sweep() -> None:
    """
    Find stuck payments and reconcile with provider.
    Handles: timeout after request, out-of-order webhook, ambiguous state.

    Interval: reconciliation_interval_seconds (default 300s = 5 min).
    """
    settings = get_settings()
    while not _shutdown.is_set():
        try:
            # TODO: Phase 8 — implement payment reconciliation
            await asyncio.sleep(settings.reconciliation_interval_seconds)
        except Exception:
            logger.exception("Reconciliation sweep error")
            await asyncio.sleep(60)


async def expiry_cleanup() -> None:
    """
    Clean up expired mandates, consents, and carts.
    Runs every 60 seconds.
    """
    while not _shutdown.is_set():
        try:
            # TODO: Phase 7 — implement expiry cleanup
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
