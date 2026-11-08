# 002. A local Eval Gate measured on in-budget solves

**Status:** Accepted (gate v1 2026-10-29; metric revised in v2 the same day)

## Context
The leaderboard is too slow and noisy to compare single changes. Locally, about half of runs went
past the 28-call cap (max 49), which the local harness does not enforce, so raw solves overstated
candidates that "solve" by overspending.

## Decision
Run candidates on a fixed 30-task set (seed 20261028) on 4× L4. Count only **in-budget solves**
(solved, ≤ 28 calls, ≤ 480 s). Compare candidates task-by-task (paired wins − losses).

## Consequences
- V14 gained 2 raw solves but 0 in-budget, so the gate held it. The metric did its job.
- Single runs move ±2–3 tasks for the same config; one run is not enough to trust a gain (see 005).
- Each run costs ~10–12 of 30 weekly GPU-quota hours.
