"""The seven metrics from Checkpoint 6.1 section 3, computed from run summaries (runs/index.jsonl).

Safety block rate and false-positive rate come from the safety eval (evals/safety), which
writes its own summary; `safety` here reports what happened inside real runs.
"""
from __future__ import annotations

from statistics import median
from typing import Iterable, Optional

from guardrails.policy import is_test_path


def _rate(num: int, den: int) -> Optional[float]:
    return None if den == 0 else round(num / den, 3)


def compute(rows: Iterable[dict]) -> dict:
    rows = list(rows)
    n = len(rows)
    if n == 0:
        return {"runs": 0}
    resolved = [r for r in rows if r.get("resolved") and not r.get("over_budget")]
    calls = [r.get("calls", 0) for r in rows]
    model_calls = sum(r.get("model_calls", 0) for r in rows)

    gold = [r for r in rows if r.get("gold_hit") is not None]
    conf = [(float(r["confidence"]), bool(r.get("tests_passed"))) for r in rows
            if r.get("confidence") is not None]
    failed_edit_runs = [r for r in rows if r.get("recovered_after_failed_edit") is not None]
    esc = [r for r in rows if r.get("status") == "ESCALATED"]
    labelled = [r for r in esc if r.get("escalation_warranted") is not None]
    reasons: dict[str, int] = {}
    for r in esc:
        reasons[r.get("escalation_reason") or "UNKNOWN"] = reasons.get(r.get("escalation_reason") or "UNKNOWN", 0) + 1
    blocked: dict[str, int] = {}
    for r in rows:
        for k, v in (r.get("blocked_reasons") or {}).items():
            blocked[k] = blocked.get(k, 0) + v

    return {
        "runs": n,
        "correctness": {"resolved_in_budget": _rate(len(resolved), n), "count": len(resolved)},
        "groundedness": {
            "gold_file_hit_rate": _rate(sum(bool(r["gold_hit"]) for r in gold), len(gold)),
            "malformed_call_rate": _rate(sum(r.get("malformed", 0) for r in rows), model_calls),
        },
        "calibration": {
            "submitted_runs": len(conf),
            "mean_confidence": round(sum(c for c, _ in conf) / len(conf), 3) if conf else None,
            "pass_rate_when_submitted": _rate(sum(p for _, p in conf), len(conf)),
            "brier": round(sum((c - p) ** 2 for c, p in conf) / len(conf), 3) if conf else None,
        },
        "safety": {
            "test_file_changes_in_final_diff": sum(
                1 for r in rows for f in (r.get("changed_files") or []) if is_test_path(f)),
            "blocked_calls": blocked,
            "runs_with_injection_flags": sum(1 for r in rows if r.get("injection_flags")),
        },
        "efficiency": {
            "median_calls": median(calls),
            "median_seconds": median([r.get("seconds", 0) for r in rows]),
            "median_tokens": median([r.get("tokens_in", 0) + r.get("tokens_out", 0) for r in rows]),
            "budget_overrun_rate": _rate(sum(1 for r in rows if r.get("over_budget")), n),
        },
        "fallback": {
            "recovered_after_failed_edit": _rate(sum(1 for r in failed_edit_runs if r["recovered_after_failed_edit"]),
                                                 len(failed_edit_runs)),
            "empty_diff_rate": _rate(sum(1 for r in rows if r.get("empty_diff")), n),
        },
        "escalation": {
            "rate": _rate(len(esc), n),
            "by_reason": reasons,
            "precision": _rate(sum(1 for r in labelled if r["escalation_warranted"]), len(labelled)),
            "labelled": len(labelled),
        },
    }
