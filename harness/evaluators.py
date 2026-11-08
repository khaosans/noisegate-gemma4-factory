"""Evaluators E1–E9 over a single task trajectory.

E1–E4 are GATE evaluators (they decide); E5–E9 are DIAGNOSTICS (they explain).
The Kaggle Eval Gate notebook is the source of truth for exact thresholds;
values marked "approx" here are documented approximations for offline analysis.
"""
from __future__ import annotations

from typing import Callable, Optional

from .trajectory import TaskResult

TEST_PATH_HINTS = ("test_", "/tests/", "_test.py", "conftest.py")


def e1_hidden_tests_pass(r: TaskResult) -> bool:
    return r.solved


def e2_within_budget(r: TaskResult) -> bool:
    return r.in_budget


def e3_source_diff(r: TaskResult) -> bool:
    return not r.empty_or_nonsource


def e4_no_test_edits(r: TaskResult) -> bool:
    return not any(h in f for f in r.src for h in TEST_PATH_HINTS)


def e5_early_first_edit(r: TaskResult) -> bool:
    return r.first_edit is not None and r.first_edit <= 10


def e6_clean_tool_args(r: TaskResult) -> bool:
    return r.malformed == 0


def e7_no_scratch_files(r: TaskResult) -> Optional[bool]:
    """approx: any edited file outside the package tree that looks like a scratch script."""
    if not r.src:
        return None
    return not any(f.startswith(("scratch", "tmp", "repro")) for f in r.src)


def e8_no_read_loops(r: TaskResult, max_reads: int = 20) -> Optional[bool]:
    """approx: flags runs whose read count dominates the budget."""
    return None if r.reads is None else r.reads <= max_reads


def e9_edited_gold_file(r: TaskResult) -> Optional[bool]:
    return r.gold


GATE: dict[str, Callable[[TaskResult], Optional[bool]]] = {
    "E1 hidden tests pass": e1_hidden_tests_pass,
    "E2 within budget": e2_within_budget,
    "E3 source diff": e3_source_diff,
    "E4 no test edits": e4_no_test_edits,
}
DIAGNOSTICS: dict[str, Callable[[TaskResult], Optional[bool]]] = {
    "E5 early first edit": e5_early_first_edit,
    "E6 clean tool args": e6_clean_tool_args,
    "E7 no scratch files": e7_no_scratch_files,
    "E8 no read loops": e8_no_read_loops,
    "E9 edited a gold file": e9_edited_gold_file,
}


def scorecard(results: list[TaskResult]) -> dict[str, dict[str, float]]:
    """Pass rate per evaluator per candidate (None results are excluded)."""
    out: dict[str, dict[str, float]] = {}
    for cand in sorted({r.candidate for r in results}):
        rows = [r for r in results if r.candidate == cand]
        card = {}
        for name, fn in {**GATE, **DIAGNOSTICS}.items():
            vals = [v for v in (fn(r) for r in rows) if v is not None]
            card[name] = round(sum(vals) / len(vals), 3) if vals else float("nan")
        out[cand] = card
    return out
