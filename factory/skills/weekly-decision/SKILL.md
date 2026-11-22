---
name: weekly-decision
description: Apply the SUBMIT/HOLD rule after screens complete. Use when a candidate has the required gate evidence and may consume today's UTC-day CreateSubmission slot.
---
# Steps
1. Build `RunSummary` objects for the candidate's runs and ALL V8 runs
   (`V8_HISTORY`, which `harness/decision_rule.py` loads from every V8 `baseline` row in
   `results/gate_runs.csv`; as of 2026-11-20 that is 8/6/8, mean 7.33). Append each new V8 run to the
   CSV first, then decide.
2. Call `harness.decision_rule.decide(...)` (or the live loop v2 / z-gate equivalent) with paired net
   and hard-check flags. Also apply `docs/wiki/Submit-Policy.md` bars (5-task vs safety vs external;
   pre-flight ≤ 11.2 h). Do not do the arithmetic by hand.
3. On a bar pass → propose a submission **only if** no CreateSubmission has been used yet this
   **UTC day** and the deadline hasn't passed. **Ask a human to approve CreateSubmission in chat and
   wait for an explicit yes**; on a scheduled wake with nobody to answer, report the proposal and stop.
4. Otherwise HOLD: mark items "held" with their numbers and report. Never submit to fill a slot.

# Submission description
"V8 + <the one change> (gate tier N, Δ=+x.x)"
