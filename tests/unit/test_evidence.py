"""
Transactra — Evidence Chain & Replay Tests

Validates:
- Hash chain integrity (append, verify, tamper detection)
- Evidence record immutability
- Chain linkage (prev_hash → record_hash)
- Replay engine: decision verification, empty chain, failure detection

All O(1) per test — no DB, no network.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.kernel.evidence.chain import (
    GENESIS_HASH,
    EvidenceChain,
    EvidenceRecord,
    EventType,
)
from backend.kernel.evidence.replay import ReplayEngine


# ═══════════════════════════════════════════════════════
# Evidence Chain
# ═══════════════════════════════════════════════════════

class TestEvidenceChain:

    def test_empty_chain(self) -> None:
        chain = EvidenceChain()
        assert chain.length == 0
        assert chain.head_hash == GENESIS_HASH
        valid, msg = chain.verify()
        assert valid

    def test_single_record(self) -> None:
        chain = EvidenceChain()
        record = chain.append("test.event", {"key": "value"})
        assert chain.length == 1
        assert record.sequence == 0
        assert record.prev_hash == GENESIS_HASH
        assert record.record_hash != GENESIS_HASH
        assert record.verify_hash()

    def test_chain_linkage(self) -> None:
        """Each record's prev_hash links to the previous record's hash."""
        chain = EvidenceChain()
        r0 = chain.append("event.first", {"n": 1})
        r1 = chain.append("event.second", {"n": 2})
        r2 = chain.append("event.third", {"n": 3})

        assert r0.prev_hash == GENESIS_HASH
        assert r1.prev_hash == r0.record_hash
        assert r2.prev_hash == r1.record_hash

    def test_verify_valid_chain(self) -> None:
        chain = EvidenceChain()
        for i in range(10):
            chain.append(f"event.{i}", {"index": i})

        valid, msg = chain.verify()
        assert valid
        assert "10 records" in msg

    def test_deterministic_hash(self) -> None:
        """Same inputs always produce the same hash."""
        chain_id = uuid4()
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)
        data = {"key": "value"}

        h1 = EvidenceRecord.compute_hash(chain_id, 0, "test", data, ts, GENESIS_HASH)
        h2 = EvidenceRecord.compute_hash(chain_id, 0, "test", data, ts, GENESIS_HASH)
        assert h1 == h2

    def test_different_data_different_hash(self) -> None:
        chain_id = uuid4()
        ts = datetime(2024, 1, 1, tzinfo=timezone.utc)

        h1 = EvidenceRecord.compute_hash(chain_id, 0, "test", {"a": 1}, ts, GENESIS_HASH)
        h2 = EvidenceRecord.compute_hash(chain_id, 0, "test", {"a": 2}, ts, GENESIS_HASH)
        assert h1 != h2

    def test_records_immutable(self) -> None:
        chain = EvidenceChain()
        record = chain.append("test", {"x": 1})
        with pytest.raises(AttributeError):
            record.data = {"tampered": True}  # type: ignore[misc]

    def test_records_tuple(self) -> None:
        chain = EvidenceChain()
        chain.append("e1", {})
        chain.append("e2", {})
        records = chain.records
        assert isinstance(records, tuple)
        assert len(records) == 2


class TestTamperDetection:

    def test_tampered_record_detected(self) -> None:
        """If a record is tampered, verify_hash returns False."""
        chain = EvidenceChain()
        record = chain.append("test", {"amount": 6_800_000})

        # Tamper: change the data
        tampered = EvidenceRecord(
            record_id=record.record_id,
            chain_id=record.chain_id,
            sequence=record.sequence,
            event_type=record.event_type,
            data={"amount": 9_999_999},  # Tampered!
            timestamp=record.timestamp,
            prev_hash=record.prev_hash,
            record_hash=record.record_hash,  # Original hash — won't match
        )
        assert not tampered.verify_hash()


class TestEventTypes:

    def test_all_event_types_defined(self) -> None:
        """Ensure all critical event types are defined."""
        assert EventType.CART_CREATED == "cart.created"
        assert EventType.AUTHORIZATION_ALLOWED == "authorization.allowed"
        assert EventType.AUTHORIZATION_DENIED == "authorization.denied"
        assert EventType.PAYMENT_PROVIDER_CONFIRMED == "payment.provider_confirmed"
        assert EventType.MANDATE_CONSUMED == "mandate.consumed"


# ═══════════════════════════════════════════════════════
# Replay Engine
# ═══════════════════════════════════════════════════════

class TestReplayEngine:

    def test_empty_chain_replay(self) -> None:
        result = ReplayEngine.verify_chain_decisions([])
        assert result.success
        assert result.total_steps == 0

    def test_valid_allow_replay(self) -> None:
        chain_records = [
            {
                "chain_id": str(uuid4()),
                "event_type": "cart.created",
                "data": {"cart_id": str(uuid4())},
            },
            {
                "chain_id": str(uuid4()),
                "event_type": "authorization.allowed",
                "data": {
                    "allowed": True,
                    "failed_rule_id": None,
                    "rule_trail": [
                        {"rule_id": "AUTH_001", "passed": True},
                        {"rule_id": "AUTH_002", "passed": True},
                    ],
                    "snapshot": {"amount": 6_800_000},
                },
            },
        ]
        result = ReplayEngine.verify_chain_decisions(chain_records)
        assert result.success
        assert result.total_steps == 1

    def test_valid_deny_replay(self) -> None:
        chain_records = [
            {
                "chain_id": str(uuid4()),
                "event_type": "authorization.denied",
                "data": {
                    "allowed": False,
                    "failed_rule_id": "AUTH_003_PRINCIPAL_ACTIVE",
                    "rule_trail": [
                        {"rule_id": "AUTH_001", "passed": True},
                        {"rule_id": "AUTH_002", "passed": True},
                        {"rule_id": "AUTH_003_PRINCIPAL_ACTIVE", "passed": False},
                    ],
                    "snapshot": {"amount": 6_800_000},
                },
            },
        ]
        result = ReplayEngine.verify_chain_decisions(chain_records)
        assert result.success

    def test_non_decision_events_skipped(self) -> None:
        chain_records = [
            {"chain_id": str(uuid4()), "event_type": "cart.created", "data": {}},
            {"chain_id": str(uuid4()), "event_type": "cart.priced", "data": {}},
            {"chain_id": str(uuid4()), "event_type": "consent.approved", "data": {}},
        ]
        result = ReplayEngine.verify_chain_decisions(chain_records)
        assert result.success
        assert result.total_steps == 0  # No decisions to verify

    def test_inconsistent_deny_detected(self) -> None:
        """If failed_rule_id is not in the rule trail, replay fails."""
        chain_records = [
            {
                "chain_id": str(uuid4()),
                "event_type": "authorization.denied",
                "data": {
                    "allowed": False,
                    "failed_rule_id": "AUTH_NONEXISTENT_RULE",
                    "rule_trail": [
                        {"rule_id": "AUTH_001", "passed": True},
                        {"rule_id": "AUTH_002", "passed": True},
                    ],
                    "snapshot": {},
                },
            },
        ]
        result = ReplayEngine.verify_chain_decisions(chain_records)
        assert not result.success
        assert result.failed_step == 0

    def test_replay_result_immutable(self) -> None:
        result = ReplayEngine.verify_chain_decisions([])
        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]
