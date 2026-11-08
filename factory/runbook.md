# Climb runbook (sanitized)

Owners: Souriya Khaosanga, Adil Shamim. Final deadline 2026-12-02 23:59 UTC.
Kaggle allows one submission per UTC day; scoring takes ~1.5 days.

**Goal:** climb from the best scored config (V8, 0.18). One submission per ISO week, and only a
candidate our own evaluation rates above V8.

## Human decisions (the loop never makes these)
- Base config. 2026-11-07: rolled back to V8; V15 lineage retired as a base.
- Cadence. 2026-11-07: one gated submission per week, two candidates screened per week.
- Final two selections for private scoring (proposed by the loop by Dec 1, chosen by humans).

## Weekly cadence (UTC)
GPU quota resets weekly (by Sat 00:30 UTC).
- **Sat — build + Run A.** Build the top two untried queue items as C1, C2 (base + one change each);
  verify source and SHA-256. Gate Run A: [C1, C2], 30 tasks.
- **Sun — Run B.** Leader = more in-budget solves (tie → fewer EMPTY_DIFF, then fewer overruns).
  Gate Run B: [V8, leader]. If both candidates were below V8's mean, Run B screens the next two items
  instead (single-run bar applies).
- **Mon — decide + submit.** Apply `harness/decision_rule.py`. Submit only on a pass.
- **Other wakes — status only.** Record new scores; refresh dashboards.
Planned submission slots: Nov 9, 16, 23, 30. No gate runs after Nov 30.

## Cost guardrails
- One gate run at a time; start one only with ≥ 12 GPU-quota hours left; two runs per quota week.
- On a run error: fix only a clear harness bug and re-run once; a second error stops the loop.
- No ad-hoc runs, larger task sets, or interactive GPU sessions.
- If the same UI step fails 3 times, stop and report.

## After a submission scores
Adopt it as the new base if its score ≥ current best (it already passed our gate, so ties go to the
candidate). Record the score and whether the gate's direction agreed with the leaderboard.

## Loop rules
1. Never delete notebooks, datasets, or submissions. Never resubmit a scored config.
2. On any unexpected state, change nothing and report.
3. End every wake with a 5-line report: scores seen, runs started/finished, verdict, submission
   (yes/no + why), GPU quota left.
