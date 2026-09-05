"""
Transactra — Trust Evidence Chain

Every significant event in a transaction produces an evidence record.
These records are hash-chained: each record includes the hash of
the previous record, creating a tamper-evident audit trail.

Complexity:
- Append evidence: O(1) hash computation
- Verify chain: O(n) where n = chain length
- Space: O(n) for chain storage

Chain structure:
  E₀ → E₁ → E₂ → ... → Eₙ
  Each Eᵢ = { event, data, timestamp, prev_hash, hash(Eᵢ) }
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """
    Single evidence record in a hash chain. Immutable.

    Contains the event type, structured data, and chain link.
    """
    record_id: UUID
    chain_id: UUID
    sequence: int
    event_type: str
    data: dict[str, Any]
    timestamp: datetime
    prev_hash: str
    record_hash: str

    def verify_hash(self) -> bool:
        """Re-compute and verify this record's hash. O(1)."""
        computed = EvidenceRecord.compute_hash(
            self.chain_id, self.sequence, self.event_type,
            self.data, self.timestamp, self.prev_hash,
        )
        return computed == self.record_hash

    @staticmethod
    def compute_hash(
        chain_id: UUID,
        sequence: int,
        event_type: str,
        data: dict[str, Any],
        timestamp: datetime,
        prev_hash: str,
    ) -> str:
        """
        Compute SHA-256 hash for an evidence record.

        Hash = SHA-256(chain_id || sequence || event || data || timestamp || prev_hash)

        Complexity: O(n) where n = data size.
        """
        canonical = json.dumps({
            "chain_id": str(chain_id),
            "sequence": sequence,
            "event_type": event_type,
            "data": data,
            "timestamp": timestamp.isoformat(),
            "prev_hash": prev_hash,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# Genesis hash constant for chain initialization
GENESIS_HASH = "0" * 64


class EvidenceChain:
    """
    Hash-chained evidence trail for a transaction.

    Append-only. Each record links to the previous via hash.
    Provides O(n) full-chain verification.

    Thread-safety: append is NOT thread-safe. Use external locking
    if concurrent appends are needed (in practice, the DB transaction
    provides this guarantee).
    """

    def __init__(self, chain_id: UUID | None = None) -> None:
        self.chain_id = chain_id or uuid4()
        self._records: list[EvidenceRecord] = []

    @property
    def length(self) -> int:
        """Number of records. O(1)."""
        return len(self._records)

    @property
    def head_hash(self) -> str:
        """Hash of the latest record, or genesis. O(1)."""
        if not self._records:
            return GENESIS_HASH
        return self._records[-1].record_hash

    @property
    def records(self) -> tuple[EvidenceRecord, ...]:
        """All records as immutable tuple. O(n)."""
        return tuple(self._records)

    def append(
        self,
        event_type: str,
        data: dict[str, Any],
        timestamp: datetime | None = None,
    ) -> EvidenceRecord:
        """
        Append a new evidence record to the chain.

        Links to the previous record's hash.

        Complexity: O(n) where n = data size for hashing.
        Amortized space: O(1) append.
        """
        ts = timestamp or datetime.now(timezone.utc)
        sequence = len(self._records)
        prev_hash = self.head_hash

        record_hash = EvidenceRecord.compute_hash(
            self.chain_id, sequence, event_type, data, ts, prev_hash
        )

        record = EvidenceRecord(
            record_id=uuid4(),
            chain_id=self.chain_id,
            sequence=sequence,
            event_type=event_type,
            data=data,
            timestamp=ts,
            prev_hash=prev_hash,
            record_hash=record_hash,
        )

        self._records.append(record)
        return record

    def verify(self) -> tuple[bool, str]:
        """
        Verify the entire chain integrity.

        Checks:
        1. Each record's hash is correctly computed
        2. Each record's prev_hash matches the previous record's hash
        3. First record's prev_hash is GENESIS_HASH

        Complexity: O(n) where n = chain length.
        Returns: (valid, error_message)
        """
        if not self._records:
            return True, "Empty chain"

        # Check genesis
        if self._records[0].prev_hash != GENESIS_HASH:
            return False, f"Record 0: prev_hash is not genesis"

        prev_hash = GENESIS_HASH
        for i, record in enumerate(self._records):
            # Check chain linkage
            if record.prev_hash != prev_hash:
                return False, (
                    f"Record {i}: prev_hash mismatch. "
                    f"Expected {prev_hash[:16]}..., got {record.prev_hash[:16]}..."
                )
            # Check hash integrity
            if not record.verify_hash():
                return False, f"Record {i}: hash verification failed"
            # Check sequence
            if record.sequence != i:
                return False, f"Record {i}: sequence mismatch ({record.sequence})"

            prev_hash = record.record_hash

        return True, f"Chain valid: {len(self._records)} records"


# ═══════════════════════════════════════════════════════
# Event Types (canonical names)
# ═══════════════════════════════════════════════════════

class EventType:
    """Canonical event type names for evidence chain."""
    CART_CREATED = "cart.created"
    CART_PRICED = "cart.priced"
    CONSENT_REQUESTED = "consent.requested"
    CONSENT_APPROVED = "consent.approved"
    CONSENT_REJECTED = "consent.rejected"
    AUTHORIZATION_REQUESTED = "authorization.requested"
    AUTHORIZATION_ALLOWED = "authorization.allowed"
    AUTHORIZATION_DENIED = "authorization.denied"
    ORDER_CREATED = "order.created"
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_PROVIDER_REQUESTED = "payment.provider_requested"
    PAYMENT_PROVIDER_CONFIRMED = "payment.provider_confirmed"
    PAYMENT_FAILED = "payment.failed"
    NEGOTIATION_STARTED = "negotiation.started"
    NEGOTIATION_OFFER_RECEIVED = "negotiation.offer_received"
    NEGOTIATION_ACCEPTED = "negotiation.accepted"
    MANDATE_CREATED = "mandate.created"
    MANDATE_CONSUMED = "mandate.consumed"
