# State, ledger and artifact contracts

What each wake reads and writes. Paths are relative to this repo unless marked **climb repo**
(the sibling [`cmu-agentic-ai`](https://github.com/khaosans/cmu-agentic-ai) checkout, which owns the
live loop state). The factory never writes into the climb repo from this repo's tooling.

**Cadence versions (record-keeping):** **loop v2** (live since 2026-11-20) is event-driven
(`jobs[]`, `plan.py`, `history.log`, KEPT14 + z-gate). **loop v1** was calendar-only
(Sat/Sun/Mon/status → 30-task noise-band gate → `results/` only); `state.v1.json` is the
rollback copy. The weekly table remains the submit-slot skeleton; human CreateSubmission is
unchanged. Wiki before/after diagrams: [`docs/wiki/Architecture.md`](../wiki/Architecture.md)
· [`docs/wiki/Claude-Cowork-Loop.md`](../wiki/Claude-Cowork-Loop.md).

| Artifact | Location | Access | Written by |
|---|---|---|---|
| Loop state | climb repo `labs/gemma-eval-harness/loop/state.json` (key `v2`) | read/write by the Cowork wake only | `plan.py`, every skill |
| Wake ledger (append-only) | climb repo `labs/gemma-eval-harness/loop/history.log` | append only | every wake |
| Narrative log | `results/eval-results.md` (mirrored to the Project doc `claude/eval-results.md`) | append only, newest at bottom | `run-eval-gate`, `weekly-decision`, `record-score` |
| Gate runs | `results/gate_runs.csv` | append only | `run-eval-gate` |
| Leaderboard | `results/leaderboard.csv` | append only | `record-score` |
| Calibration | table in `results/README.md` | append row | `record-score` |
| Candidates | `product/candidates.md` | mark tried / held | `build-candidate`, `weekly-decision` |
| Climb scoreboard | climb repo `docs/scoreboard.json` | **read-only** from here | climb repo `scripts/refresh_scoreboard.py` |

## Loop state (`state.json`, key `v2`)
- `jobs[]`: `{id, cands, task_set, repeats, priority, not_before, due_by, after, status, est_q_h, est_wall_h}`.
  `task_set` is `KEPT14` (or `KEPT14p` for a capped partial run; its paired wins/losses count, its counts
  stay out of the means). `status` ∈ planned / late / running / done / skipped.
- `pipeline[]`: one-change ideas `{id, status, change, targets, evidence, next}`; `status` ∈ idea / ready /
  built / confirming / closed. Keep ≥ 3 open.
- Rollback copy: `state.v1.json`. Never edit state by hand outside a wake; on unexpected state, change nothing and report.

## Wake ledger (`history.log`)
One line per wake, never rewritten: `{planned, fired, lag_min, kind, action, quota}`, where `action` is the
`plan.py next` result (START / WAIT / PARSE / DEFER / IDLE / SKIP) and `quota` is used/30 h.
`plan.py audit` reads it.

## CSV schemas
- `gate_runs.csv`: `gate_run,kaggle_run_id,date,baseline,candidate,solved,in_budget,empty_diff,edit_fail,logic_mismatch,timeout,over_28_calls,paired_net_vs_baseline,verdict` — counts per task set of that run.
- `leaderboard.csv`: `version,kaggle_run_id,submitted_utc,public_score,change,notes`.

## `eval-results.md` entry template
```
## YYYY-MM-DD — <what happened> (<gate vN>, run <id>)
| Candidate | Change (off base) | Solved | In-budget | Empty/non-source | Overruns | Test edits |
- Paired net vs V8, decision (tier / z / failed check), next step, GPU quota used/30 h.
```

## Climb bridge (`docs/scoreboard.json`, read-only)
Factory SoT is **V8 @ 0.18**. The climb repo's scoreboard tracks its own tip and may show a different
best (e.g. 0.10); never copy that number into `results/` and never write to the climb ledger from here.
