"""Structured, append-only audit trail (JSON Lines).

Every record carries who did what, when, from which session, and with which filters,
so that a reviewer can reconstruct any export or alert decision. Records are written
one JSON object per line, which log shippers (Fluent Bit, Filebeat, Loki) ingest
directly. Each record also carries a SHA-256 chain hash of the previous record so
deletions or edits inside the file are detectable with :func:`verify_chain`.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GENESIS = "0" * 64

# Keys whose values must never reach the log.
_SECRET_KEYS = re.compile(r"pass(word)?|secret|token|api[_-]?key|authorization|cookie", re.IGNORECASE)
_MAX_VALUE_LEN = 2000


def redact(value: Any) -> Any:
    """Recursively drop secrets and bound value sizes before logging."""
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if _SECRET_KEYS.search(str(k)) else redact(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    s = str(value)
    return s if len(s) <= _MAX_VALUE_LEN else s[:_MAX_VALUE_LEN] + "…"


def _digest(prev: str, body: str) -> str:
    return hashlib.sha256((prev + body).encode("utf-8")).hexdigest()


class AuditLogger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._last = self._read_last_hash()

    def _read_last_hash(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return GENESIS
        with self.path.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 65536))
            tail = fh.read().decode("utf-8", errors="ignore").strip().splitlines()
        for line in reversed(tail):
            try:
                return json.loads(line)["hash"]
            except (ValueError, KeyError):
                continue
        return GENESIS

    def log(
        self,
        event: str,
        *,
        user: str | None = None,
        role: str | None = None,
        session_id: str | None = None,
        outcome: str = "success",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "event": event,
            "user": user or "anonymous",
            "role": role or "none",
            "session": session_id or "",
            "outcome": outcome,
            "details": redact(details or {}),
        }
        with self._lock:
            body = json.dumps(record, sort_keys=True, ensure_ascii=False, default=str)
            record["prev"] = self._last
            record["hash"] = _digest(self._last, body)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, sort_keys=True, ensure_ascii=False, default=str) + "\n")
            self._last = record["hash"]
        return record


def verify_chain(lines: Iterable[str]) -> bool:
    """Return True if every record's hash matches its content and predecessor."""
    prev = GENESIS
    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        claimed, claimed_prev = rec.pop("hash"), rec.pop("prev")
        if claimed_prev != prev:
            return False
        body = json.dumps(rec, sort_keys=True, ensure_ascii=False, default=str)
        if _digest(prev, body) != claimed:
            return False
        prev = claimed
    return True
