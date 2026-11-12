"""Structured JSONL run logs: the source of truth for AgentOps queries.

Layout (default root `runs/`, git-ignored):
  runs/events/<run_id>.jsonl   one line per step: model call, tool call + guard verdict, verify, escalation
  runs/index.jsonl             one summary line per finished run

LangSmith (optional) sees the same run as a trace tree; this log works offline and with no account.
"""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

_SECRET_PATTERNS = [
    re.compile(r"\b(sk|rk|pk)-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bhf_[A-Za-z0-9]{20,}"),
    re.compile(r"\bls(v2)?_[a-z]{2}_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
]


def redact(value: Any) -> Any:
    """Mask likely secrets in strings, recursively in dicts and lists."""
    if isinstance(value, str):
        out = value
        for rx in _SECRET_PATTERNS:
            out = rx.sub("[REDACTED]", out)
        return out
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    return value


def default_root() -> Path:
    return Path(os.environ.get("NOISEGATE_RUNS_DIR", "runs"))


class RunLog:
    def __init__(self, task_id: str, config: str, root: str | Path | None = None,
                 run_id: str | None = None):
        self.root = Path(root) if root else default_root()
        self.run_id = run_id or f"{time.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6]}"
        self.task_id = task_id
        self.config = config
        self.seq = 0
        (self.root / "events").mkdir(parents=True, exist_ok=True)
        self.path = self.root / "events" / f"{self.run_id}.jsonl"

    def event(self, kind: str, **fields: Any) -> dict:
        self.seq += 1
        rec = {"ts": round(time.time(), 3), "run_id": self.run_id, "task_id": self.task_id,
               "config": self.config, "seq": self.seq, "kind": kind, **redact(fields)}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        return rec

    def summary(self, **fields: Any) -> dict:
        rec = {"run_id": self.run_id, "task_id": self.task_id, "config": self.config,
               "ts": round(time.time(), 3), **redact(fields)}
        with (self.root / "index.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        return rec


def read_jsonl(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
