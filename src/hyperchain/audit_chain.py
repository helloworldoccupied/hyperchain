"""ECC Audit Chain — Layer 2: immutable hash-chained audit trail."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import AuditIntegrityError

GENESIS_HASH = "sha256:genesis"


def _sha256(data: str) -> str:
    """Return sha256:hex digest of a string."""
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


def _content_hash(entry: dict) -> str:
    """Compute the canonical hash of an entry (excluding its own 'hash' field)."""
    clone = {k: v for k, v in entry.items() if k != "hash"}
    return "sha256:" + hashlib.sha256(
        json.dumps(clone, sort_keys=True).encode()
    ).hexdigest()


class AuditChain:
    """Append-only, hash-chained audit log."""

    def __init__(self, storage: Path | None = None):
        self._entries: list[dict[str, Any]] = []
        self._storage = Path(storage) if storage else None

    @property
    def entries(self) -> list[dict[str, Any]]:
        return self._entries

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(
        self,
        task_id: str,
        actor: str,
        action: str,
        evidence: str | None = None,
        input_data: str | None = None,
        output_data: str | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        """Append an auditable entry to the chain."""
        prev_hash = self._entries[-1]["hash"] if self._entries else GENESIS_HASH

        entry: dict[str, Any] = {
            "task_id": task_id,
            "actor": actor,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prev_hash": prev_hash,
        }

        if evidence is not None:
            entry["evidence"] = evidence

        if input_data is not None:
            entry["input_hash"] = _sha256(input_data)

        if output_data is not None:
            entry["output_hash"] = _sha256(output_data)

        if extra:
            entry.update(extra)

        entry["hash"] = _content_hash(entry)
        self._entries.append(entry)
        return entry

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    def verify_integrity(self) -> bool:
        """Walk the chain and verify every hash link. Raises AuditIntegrityError on failure."""
        expected_prev = GENESIS_HASH
        for idx, entry in enumerate(self._entries):
            # Check prev_hash linkage
            if entry["prev_hash"] != expected_prev:
                raise AuditIntegrityError(idx, expected_prev, entry["prev_hash"])
            # Recompute content hash
            recomputed = _content_hash(entry)
            if entry["hash"] != recomputed:
                raise AuditIntegrityError(idx, recomputed, entry["hash"])
            expected_prev = entry["hash"]
        return True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist chain to storage/chain.json."""
        if self._storage is None:
            raise ValueError("No storage path configured")
        self._storage.mkdir(parents=True, exist_ok=True)
        path = self._storage / "chain.json"
        path.write_text(json.dumps(self._entries, indent=2, ensure_ascii=False), encoding="utf-8")

    def load(self) -> None:
        """Load chain from storage/chain.json."""
        if self._storage is None:
            raise ValueError("No storage path configured")
        path = self._storage / "chain.json"
        self._entries = json.loads(path.read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_report(
        self,
        task_id: str,
        output_path: Path | str,
        format: str = "json",  # noqa: A002
    ) -> Path:
        """Export filtered entries for a single task."""
        output_path = Path(output_path)
        filtered = [e for e in self._entries if e["task_id"] == task_id]
        report = {"task_id": task_id, "entries": filtered}
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return output_path
