# Climb runbook (sanitized)

Owners: Souriya Khaosanga, Adil Shamim. Final deadline 2026-12-02 23:59 UTC.
Kaggle allows one submission per UTC day; scoring takes ~1.5 days.

**Goal:** climb from the best scored config (V8, 0.18). At most **one CreateSubmission per UTC day**
(Kaggle), and only when the candidate clears the current quality bars (`docs/wiki/Submit-Policy.md`).

## Current state (2026-11-21) — read first on every wake
- Base: **V8 @ 0.18** (best scored). V8–V23 evaluated; scored: V11 0.15, V12 0.15, V15 0.17, V20 0.13.
- **Submit policy (live):** host **1 / UTC day** only — no factory 36 h gap, 3-per-week cap, or
  wait-for-score lock. V8-derived prompt/sampling/budget tips: **5-task** screen; **7-task safety**
  only if tools/edit-mechanics flagged; external configs need a **strict win** vs V8 (settings may
  transplant; prompt never submitted). Pre-flight incl. ≤ 11.2 h. Detail: `docs/wiki/Submit-Policy.md`.
- Loop v2 is live (event-driven jobs, KEPT14, z-gate; see `state-and-artifacts.md`). The weekly table
  below is a **work skeleton**, not the submit-slot law.

## Human decisions (the loop never makes these)
- Base config. 2026-11-07: rolled back to V8; V15 lineage retired as a base.
- Cadence / bar policy (document changes in Submit-Policy; do not silently re-tighten).
- Final two selections for private scoring (proposed by the loop by Dec 1, chosen by humans).
- **CreateSubmission.** The loop prepares the version and description; a human approves in chat before
  it is clicked. Consoles (Ops Console, legacy `factory_console/`) never submit.

## Weekly work skeleton (UTC)
GPU quota resets weekly (by Sat 00:30 UTC).
- **Sat — build + Run A.** Build the top untried queue items; verify source and SHA-256; screen.
- **Sun — Run B / confirms.** Paired runs vs V8 as jobs require.
- **Mon — decide + optional submit.** Apply the coded rule / z-gate and Submit-Policy bars. On a
  pass, ask a human to approve CreateSubmission (**1 / UTC day**); never submit on HOLD.
- **Other wakes — status only.** Record new scores; refresh dashboards.
Skill order on a full week: `build-candidate` → `run-eval-gate` → `weekly-decision` → `record-score`.
State, ledger and file schemas: `state-and-artifacts.md`.
Planned submission slots: Nov 9, 16, 23, 30 (calendar hints under **1 / UTC day** Submit-Policy; not a weekly-only cap).
No gate runs after Nov 30.

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
