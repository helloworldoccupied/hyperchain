"""Tests for ECC Audit Chain (Layer 2)."""

import json
import pytest

from hyperchain.audit_chain import AuditChain
from hyperchain.errors import AuditIntegrityError


class TestRecord:
    """Tests for recording audit entries."""

    def test_creates_entry(self):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="write_code")
        assert len(chain.entries) == 1
        entry = chain.entries[0]
        assert entry["task_id"] == "t1"
        assert entry["actor"] == "claude"
        assert entry["action"] == "write_code"

    def test_auto_timestamps(self):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="review")
        entry = chain.entries[0]
        assert "timestamp" in entry
        assert isinstance(entry["timestamp"], str)
        assert len(entry["timestamp"]) > 0

    def test_includes_hash(self):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="deploy")
        entry = chain.entries[0]
        assert "hash" in entry
        assert entry["hash"].startswith("sha256:")

    def test_second_entry_chains_to_first(self):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="write")
        chain.record(task_id="t1", actor="codex", action="review")
        first = chain.entries[0]
        second = chain.entries[1]
        assert second["prev_hash"] == first["hash"]

    def test_first_entry_prev_hash_is_genesis(self):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="init")
        assert chain.entries[0]["prev_hash"] == "sha256:genesis"

    def test_record_with_evidence(self):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="test", evidence="all 12 tests passed")
        entry = chain.entries[0]
        assert entry["evidence"] == "all 12 tests passed"

    def test_record_with_input_output_hashes(self):
        chain = AuditChain()
        chain.record(
            task_id="t1",
            actor="claude",
            action="transform",
            input_data="raw input",
            output_data="processed output",
        )
        entry = chain.entries[0]
        assert "input_hash" in entry
        assert "output_hash" in entry
        assert entry["input_hash"].startswith("sha256:")
        assert entry["output_hash"].startswith("sha256:")
        assert entry["input_hash"] != entry["output_hash"]


class TestIntegrity:
    """Tests for chain integrity verification."""

    def test_verify_intact_chain(self):
        chain = AuditChain()
        chain.record(task_id="t1", actor="a", action="step1")
        chain.record(task_id="t1", actor="b", action="step2")
        chain.record(task_id="t1", actor="c", action="step3")
        assert chain.verify_integrity() is True

    def test_verify_detects_tampering(self):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="write")
        chain.record(task_id="t1", actor="codex", action="review")
        # Tamper with the first entry
        chain.entries[0]["actor"] = "TAMPERED"
        with pytest.raises(AuditIntegrityError):
            chain.verify_integrity()

    def test_verify_empty_chain(self):
        chain = AuditChain()
        assert chain.verify_integrity() is True


class TestPersistence:
    """Tests for save/load functionality."""

    def test_save_and_load(self, tmp_path):
        chain = AuditChain(storage=tmp_path)
        chain.record(task_id="t1", actor="claude", action="write")
        chain.record(task_id="t1", actor="codex", action="review")
        chain.save()

        chain2 = AuditChain(storage=tmp_path)
        chain2.load()
        assert len(chain2.entries) == 2
        assert chain2.entries[0]["task_id"] == "t1"
        assert chain2.entries[1]["action"] == "review"
        assert chain2.verify_integrity() is True


class TestExport:
    """Tests for report export."""

    def test_export_json(self, tmp_path):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="write")
        chain.record(task_id="t1", actor="codex", action="review")
        out = tmp_path / "report.json"
        chain.export_report(task_id="t1", output_path=out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["task_id"] == "t1"
        assert len(data["entries"]) == 2

    def test_export_filters_by_task(self, tmp_path):
        chain = AuditChain()
        chain.record(task_id="t1", actor="claude", action="write")
        chain.record(task_id="t2", actor="codex", action="review")
        chain.record(task_id="t1", actor="claude", action="deploy")
        out = tmp_path / "report.json"
        chain.export_report(task_id="t1", output_path=out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["task_id"] == "t1"
        assert len(data["entries"]) == 2
        assert all(e["task_id"] == "t1" for e in data["entries"])
