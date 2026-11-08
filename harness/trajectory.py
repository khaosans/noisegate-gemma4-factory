"""Parse Eval Gate per-task log lines into typed records.

Line format (gate v3+; each line is printed twice, so dedupe):
HH:MM:SS  Score  <cand> <task> repN: <MODE> solved=<bool> calls=<n> first_edit=<n|None>
malformed=<n> dur=<s>s reads=<n> badedits=<n> post=<n> tok=<n> gold=<bool|None> src=<a;b>

Gate v1/v2 logs lack reads/badedits/post/tok/gold; those fields parse as None.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

from pydantic import BaseModel

CALL_BUDGET = 28
TIME_BUDGET_S = 480

_LINE = re.compile(
    r"Score\s+(?P<candidate>\S+)\s+(?P<task>\S+)\s+rep(?P<rep>\d+):\s+(?P<mode>\S+)\s+(?P<kv>.*)$"
)
_KV = re.compile(r"(\w+)=(\S*)")


def _num(v: Optional[str]) -> Optional[float]:
    if v is None or v in ("", "None"):
        return None
    return float(v.rstrip("s"))


def _bool(v: Optional[str]) -> Optional[bool]:
    if v is None or v in ("", "None"):
        return None
    return v == "True"


class TaskResult(BaseModel):
    candidate: str
    task: str
    rep: int
    mode: str  # e.g. SOLVED, EMPTY_DIFF, EDIT_FAIL, LOGIC_MISMATCH, TIMEOUT
    solved: bool
    calls: int
    first_edit: Optional[int] = None
    malformed: int = 0
    dur_s: float
    reads: Optional[int] = None
    badedits: Optional[int] = None
    post: Optional[int] = None
    tok: Optional[int] = None
    gold: Optional[bool] = None
    src: list[str] = []

    @property
    def in_budget(self) -> bool:
        return self.calls <= CALL_BUDGET and self.dur_s <= TIME_BUDGET_S

    @property
    def in_budget_solve(self) -> bool:
        """The gate metric: solved within 28 calls and 480 s."""
        return self.solved and self.in_budget

    @property
    def empty_or_nonsource(self) -> bool:
        return self.mode == "EMPTY_DIFF" or not self.src


def parse_line(line: str) -> Optional[TaskResult]:
    m = _LINE.search(line)
    if not m:
        return None
    kv = dict(_KV.findall(m.group("kv")))
    as_int = lambda k: None if _num(kv.get(k)) is None else int(_num(kv.get(k)))
    src = kv.get("src", "")
    return TaskResult(
        candidate=m.group("candidate"),
        task=m.group("task"),
        rep=int(m.group("rep")),
        mode=m.group("mode"),
        solved=bool(_bool(kv.get("solved"))),
        calls=as_int("calls") or 0,
        first_edit=as_int("first_edit"),
        malformed=as_int("malformed") or 0,
        dur_s=_num(kv.get("dur")) or 0.0,
        reads=as_int("reads"),
        badedits=as_int("badedits"),
        post=as_int("post"),
        tok=as_int("tok"),
        gold=_bool(kv.get("gold")),
        src=[s for s in src.split(";") if s and s != "None"],
    )


def parse_log(lines: Iterable[str]) -> list[TaskResult]:
    """Parse and dedupe (each Score line appears twice in Kaggle output)."""
    seen: dict[tuple[str, str, int], TaskResult] = {}
    for line in lines:
        r = parse_line(line)
        if r is not None:
            seen[(r.candidate, r.task, r.rep)] = r
    return list(seen.values())
