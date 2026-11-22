# 005. One gated submission per week, two runs per decision

**Status:** Partially superseded (2026-11-21). **Quality tiers / paired evidence** remain; the
**homemade cadence caps** (≤1 submit / ISO week, and later 36 h / 3-per-week / wait-for-score) were
retired in favor of Kaggle’s **1 / UTC day** + [[Submit-Policy]](../wiki/Submit-Policy.md) bars.
Original acceptance: 2026-11-07 (human decision).

## Context
Gate noise ±2–3 tasks/30, leaderboard noise ±0.05, 30 GPU-quota hours per week, ~11 h per run.

## Decision
Each week: screen two candidates (Run A), confirm the leader against V8 (Run B), then submit only
if Δ ≥ +1.0 in-budget solves/30 over two runs with Run B paired net ≥ 0 (Tier 2), or Δ ≥ +2.5
(Tier 1). Otherwise no submission that week. Implemented in `harness/decision_rule.py`.

## Consequences
- At most four more submissions before the Dec 2 deadline; some weeks will submit nothing.
- Uses ~22–24 of 30 quota hours per week, within guardrails.
- Passing makes an improvement likely, not certain; we log whether each pass agrees with the
  leaderboard (calibration).
