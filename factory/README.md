# Factory: the loop that builds, judges, and ships the product

Claude runs the climb loop inside a claude.ai Project on scheduled wakes. It proposes candidates,
builds them on Kaggle, runs the Eval Gate, applies the decision rule, and submits at most once a week.
Humans set the base, the cadence, and the final selections.

```
 queue item ──► build-candidate ──► run-eval-gate (Run A: screen 2)
                                          │
                                          ▼
                                    run-eval-gate (Run B: leader vs V8)
                                          │
                                          ▼
                                    weekly-decision ──HOLD──► report to humans
                                          │ SUBMIT
                                          ▼
                                 Kaggle submission (≤ 1/week)
                                          │ ~1.5 days
                                          ▼
                                    record-score ──► new base? (LB ≥ best) ──► next queue item
```

| Piece | File |
|---|---|
| System prompt for the Project | `project-instructions.md` |
| Operating procedure, cadence, guardrails | `runbook.md` |
| Procedures as loadable skills | `skills/*/SKILL.md` |
| Persistent memory | `../results/eval-results.md`, `../results/*.csv` |
| Decision logic as code | `../harness/decision_rule.py` |
