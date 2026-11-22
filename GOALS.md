# Goals (OKRs)

Key results are set on things we can measure above the noise. "Beat 0.18" alone is not one:
the same config can land ±0.05 apart. Status is updated by the `record-score` skill.

| Objective | Key result | Status (2026-11-07) |
|---|---|---|
| **O1. Ship an agent that is genuinely better than V8** | A candidate passes gate Tier 1 or 2 by Nov 30 | Not yet (V14, V16, V17 held) |
| | Leaderboard best ≥ 0.23 (above V8 by more than noise) by Dec 2 | 0.18 |
| | Submitted candidate's EMPTY_DIFF per 30 below V8's mean (8.0) | — |
| **O2. Trust our own evaluation** | ≥ 2 of 3 scored points agree in direction with the leaderboard | 1 agree, 1 disagree, 1 inconclusive |
| | 0 submissions that did not pass the gate (from Nov 7) | On track |
| **O3. Run the factory frugally** | ≤ 2 gate runs and ≤ 24 GPU-quota h per week; ≤ 1 CreateSubmission / **UTC day** (host) + Submit-Policy bars | On track |
| | 0 unrecovered harness errors | On track |
| **O4. Make it reproducible for the class** | A reader rebuilds V8's four files from this repo and matches their SHA-256 in < 15 min | Pending (files to be exported) |
