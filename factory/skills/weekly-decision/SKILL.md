---
name: weekly-decision
description: Apply the weekly SUBMIT/HOLD rule after Run B completes. Use on the Monday wake, or whenever a candidate has two gate runs this ISO week.
---
# Steps
1. Build `RunSummary` objects for the candidate's runs this week and ALL V8 runs
   (`V8_HISTORY` plus each week's Run B V8 row).
2. Call `harness.decision_rule.decide(...)` with the Run B paired net and the hard-check flags
   (zip SHA-256 matches, one change off base, never scored). Do not do the arithmetic by hand.
3. Tier 1 (Δ ≥ +2.5, paired net ≥ 0) or Tier 2 (Δ ≥ +1.0, paired net ≥ 0) → submit, if no team
   submission exists this ISO week and the deadline hasn't passed.
4. Otherwise HOLD: mark both items "held" with their numbers and report. Never submit just to fill
   the weekly slot.

# Submission description
"V8 + <the one change> (gate tier N, Δ=+x.x)"
