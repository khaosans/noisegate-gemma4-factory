# Factory: the loop that builds, judges, and ships the product

Claude runs the climb loop inside a claude.ai Project on scheduled wakes. It proposes candidates,
builds them on Kaggle, runs the Eval Gate, applies the decision rule, and submits at most once a week.
Humans set the base, the cadence, and the final selections.

Diagram story (Figure 1 three-band + weekly turn): [Architecture wiki](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Architecture) · [Claude Cowork Loop](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Claude-Cowork-Loop).

```mermaid
flowchart TB
  Q[Queue item] --> BC[build-candidate]
  BC --> GA[run-eval-gate Run A<br/>screen 2]
  GA --> GB[run-eval-gate Run B<br/>leader vs V8 · else next pair]
  GB --> WD{weekly-decision}
  WD -->|HOLD| RH[Report to humans]
  WD -->|SUBMIT| KS[Human-approved submission ≤ 1/week]
  KS --> Wait[~1.5 days]
  Wait --> RS[record-score]
  RS -->|LB ≥ best| NB[New base → next queue item]

  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  classDef hold fill:#F3F4F6,stroke:#6B7280,color:#374151
  class Q,BC,GA,GB,WD,Wait,RS,NB factory
  class KS hitl
  class RH hold
```

*Insight.* Run A screens; Run B pairs a leader vs V8 (or the next pair if both trail). HOLD is success when the gain is inside noise.

| Piece | File |
|---|---|
| System prompt for the Project | `project-instructions.md` |
| Operating procedure, cadence, guardrails | `runbook.md` |
| Procedures as loadable skills | `skills/*/SKILL.md` |
| State, ledger, file schemas | `state-and-artifacts.md` |
| Persistent memory | `../results/eval-results.md`, `../results/*.csv` |
| Decision logic as code | `../harness/decision_rule.py` |
