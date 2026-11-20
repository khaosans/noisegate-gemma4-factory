---
name: weekly-decision
description: Apply the weekly SUBMIT/HOLD rule after Run B completes. Use on the Monday wake, or whenever a candidate has two gate runs this ISO week.
---
# Steps
1. Build `RunSummary` objects for the candidate's runs this week and ALL V8 runs
   (`V8_HISTORY`, which `harness/decision_rule.py` loads from every V8 `baseline` row in
   `results/gate_runs.csv`; as of 2026-11-20 that is 8/6/8, mean 7.33). Append each new V8 run to the
   CSV first, then decide.
2. Call `harness.decision_rule.decide(...)` with the Run B paired net and the hard-check flags
   (zip SHA-256 matches, one change off base, never scored). Do not do the arithmetic by hand.
3. Tier 1 (Δ ≥ +2.5, paired net ≥ 0) or Tier 2 (Δ ≥ +1.0, paired net ≥ 0) → propose a submission, if no
   team submission exists this ISO week and the deadline hasn't passed. **Ask a human to approve
   CreateSubmission in chat and wait for an explicit yes**; on a scheduled wake with nobody to answer,
   report the proposal and stop. (Loop v2 expresses the same tiers as z: T2 z ≥ 1.0 over ≥ 2 runs,
   SINGLE z ≥ 2.5, CONFIRM z ≥ 0.75 → one more paired run.)
4. Otherwise HOLD: mark both items "held" with their numbers and report. Never submit just to fill
   the weekly slot.

# Submission description
"V8 + <the one change> (gate tier N, Δ=+x.x)"
