"""Weekly SUBMIT / HOLD rule for the climb loop.

Metric: in-budget solves per 30 tasks (solved, calls <= 28, dur <= 480 s).
Delta = candidate mean over its runs this week - V8 mean over ALL V8 runs.

Why the margins: single-run gate noise is about +/-2-3 tasks per 30 (the same V15
config scored 7 then 10), and leaderboard noise is about +/-0.05 (a public 0.22
config scored 0.17 for us). Passing makes an improvement likely, not certain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Optional

from .trajectory import TaskResult


@dataclass
class RunSummary:
    in_budget_solves: int
    empty_or_nonsource: int
    overruns: int  # runs over 28 calls or 480 s
    harness_errors: int = 0
    stopped_early: bool = False
    test_file_edits: int = 0

    @classmethod
    def from_results(cls, rows: list[TaskResult]) -> "RunSummary":
        return cls(
            in_budget_solves=sum(r.in_budget_solve for r in rows),
            empty_or_nonsource=sum(r.empty_or_nonsource for r in rows),
            overruns=sum(not r.in_budget for r in rows),
        )


@dataclass
class Decision:
    verdict: str  # "SUBMIT tier 1" | "SUBMIT tier 2" | "SUBMIT single-run" | "HOLD"
    delta: float
    reasons: list[str] = field(default_factory=list)


def paired_net(candidate: list[TaskResult], base: list[TaskResult]) -> int:
    """Wins minus losses on in-budget solves, matched by task (same run)."""
    b = {r.task: r.in_budget_solve for r in base}
    wins = sum(1 for r in candidate if r.task in b and r.in_budget_solve and not b[r.task])
    losses = sum(1 for r in candidate if r.task in b and not r.in_budget_solve and b[r.task])
    return wins - losses


def decide(
    candidate_runs: list[RunSummary],
    v8_runs: list[RunSummary],
    run_b_paired_net: Optional[int],
    zip_sha_ok: bool,
    one_change_off_base: bool,
    never_scored: bool,
    single_run_screen: bool = False,
) -> Decision:
    v8_mean = mean(r.in_budget_solves for r in v8_runs)
    cand_mean = mean(r.in_budget_solves for r in candidate_runs)
    delta = round(cand_mean - v8_mean, 2)
    reasons: list[str] = []

    v8_empty = mean(r.empty_or_nonsource for r in v8_runs)
    v8_over = mean(r.overruns for r in v8_runs)
    if mean(r.empty_or_nonsource for r in candidate_runs) > v8_empty + 1:
        reasons.append("EMPTY_DIFF/non-source worse than V8 mean + 1")
    if mean(r.overruns for r in candidate_runs) > v8_over + 1:
        reasons.append("budget overruns worse than V8 mean + 1")
    if any(r.test_file_edits for r in candidate_runs):
        reasons.append("edited test files")
    if any(r.harness_errors or r.stopped_early for r in candidate_runs):
        reasons.append("harness error or run stopped early")
    if not zip_sha_ok:
        reasons.append("zip SHA-256 does not match the built version")
    if not one_change_off_base:
        reasons.append("not exactly one change off the current base")
    if not never_scored:
        reasons.append("config already scored; never resubmit")
    if reasons:
        return Decision("HOLD", delta, reasons)

    if single_run_screen:
        if len(candidate_runs) == 1 and delta >= 4.0:
            return Decision("SUBMIT single-run", delta)
        return Decision("HOLD", delta, ["single-run bar is delta >= +4.0"])

    if len(candidate_runs) < 2 or run_b_paired_net is None:
        return Decision("HOLD", delta, ["needs two runs and a Run B paired comparison"])
    if run_b_paired_net < 0:
        return Decision("HOLD", delta, [f"Run B paired net {run_b_paired_net} < 0"])
    if delta >= 2.5:
        return Decision("SUBMIT tier 1", delta)
    if delta >= 1.0:
        return Decision("SUBMIT tier 2", delta)
    return Decision("HOLD", delta, [f"delta {delta:+.2f} below +1.0"])


# Historical V8 runs (gate v1, gate v4). Append each week's Run B.
V8_HISTORY = [
    RunSummary(in_budget_solves=8, empty_or_nonsource=7, overruns=16),
    RunSummary(in_budget_solves=6, empty_or_nonsource=9, overruns=18),
]
