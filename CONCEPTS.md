# Course concepts → where they live in this repo

Each row points to code or data, not just a claim. Rows marked *not used* are deliberate.

## Two agents, so two of everything

| | Product (Gemma 4 SuperAgent) | Factory (Claude climb loop) |
|---|---|---|
| Model | gemma-4-31b-it (fixed by the rules) | Claude |
| Harness | Kaggle agent runtime + `product/superagent/agent.yaml` | claude.ai Project + scheduled wakes |
| Tools | `edit_file`, shell, `git grep`, `submit_patch` | Kaggle notebooks, browser, dashboards |
| Procedures | call plan in `prompts/system.md` | `factory/skills/*/SKILL.md` |
| Memory | context window only | `results/` (CSV + dated log) |
| Guardrails | 28 calls, 8 min, zero-diff rule | GPU quota, 1 run at a time, ≤ 1 submission/week |
| Evaluation | hidden tests (leaderboard) | Eval Gate + E1–E9 + decision rule |
| Human in the loop | — | base, cadence, final picks |

## Concept map

| Concept | Where | What the evidence shows |
|---|---|---|
| Agent loop / ReAct | `product/superagent/prompts/system.md` | locate → edit by call 7 → verify → submit |
| Tool design (agent-computer interface) | `product/candidates.md` (V16), `docs/decisions/006` | removing unused tools didn't break anything (net −1, noise) |
| Planning under a budget | call plan, 28-call cap | median first edit ≈ call 15–17; late edits → EMPTY_DIFF |
| Context engineering | `configs/sampling.yaml` | thinking-budget cuts (V11/V12) scored 0.15 vs 0.18 |
| Constraints: prompt vs tool layer | V17, `docs/decisions/006` | prompt deadline ignored (8 of 9 empty runs still late) |
| Skills / procedural memory | `factory/skills/` | runbook split into 4 loadable procedures |
| Persistent memory | `results/` | the loop's state survives between wakes |
| Trajectory evaluation | `harness/trajectory.py`, `harness/evaluators.py` | E1–E4 gate, E5–E9 diagnose |
| Statistical rigor | `harness/decision_rule.py`, `docs/decisions/005` | same config moves ±3 tasks; two runs + paired test required |
| Calibration | `results/README.md` | 1 of 2 decisive points agreed with the leaderboard |
| Guardrails & cost control | `factory/runbook.md` | ~11 GPU-h per run, 2 runs/week |
| Human-in-the-loop | `factory/runbook.md`, `docs/decisions/004` | rollback to V8 was a human call |
| Self-improving systems | `factory/` | qualified: it proposes and tests; humans decide what ships |
| Multi-agent / supervisor | *not used in the submission* | the product is one Gemma agent with a fixed call plan |
