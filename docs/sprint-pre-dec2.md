# Pre–Dec 2, 2026 sprint (public)

Competition deadline: **2026-12-02 23:59 UTC**. This page is the public sprint checklist for NoiseGate. Live design SoT remains the [wiki](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Home), [Submit-Policy](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Submit-Policy), and [Architecture](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Architecture).

## Public surface (OK to publish)

| Area | In this repo |
|---|---|
| Harness / loaders / eval | `harness/`, `evals/`, `results/` bookkeeping |
| Baselines & noise band | V8 history, Trajectory rubric, gate charts |
| Architecture & governance | Wiki Mermaid, factory ledger schemas, HITL tiers |
| Guardrails (code) | `guardrails/` allow-lists, budgets, shell policy — **model proposes; code decides** |
| Ship-path ADK config | `product/` zip builder + shipped `system.md` for the competition agent |

## Private surface (not NoiseGate)

Keep in the private sibling [`cmu-agentic-ai`](https://github.com/khaosans/cmu-agentic-ai) unless an owner explicitly asks to publish:

- Tuned prompt experiments, heuristic sweeps, ensemble weights
- Leakage / contamination finds against hidden tasks
- Climb tip packages, raw scoreboard mutations, GPU tokens
- Course IP / syllabus text

Consoles and the climb bridge stay **read-only / non-submitting** on the public side.

## Tool-layer guardrails & verification (current)

Already on `main` (course / local reference — **not** inside the Kaggle zip unless noted):

| Control | Where | Notes |
|---|---|---|
| Policy ALLOW / BLOCK / ESCALATE | `guardrails/policy.py` | Path + tool allow-list |
| Shell allow-list | `guardrails/shell.py` | Network / secret / destructive blocks |
| Budgets | `guardrails/budget.py` | ≤28 calls · ≤480s (product contract) |
| Untrusted input delimit | `guardrails/untrusted.py` | Flags injection phrases; does not trust the model |
| Patch checks | `guardrails/output.py` | Workspace / test-file constraints |
| Mid-run interception | `supervisor/graph.py` `guard` + `hitl` | Local LangGraph only; Kaggle host owns outer loop |
| Safety eval | `evals/safety/` | Adversarial + benign twins |

**Not yet on `main` (blocked on missing sync bundles):** Checkpoint 6.1 patch-quality / soft-tier / review-packet commits; SWE-bench Lite pre-gate runner. Do **not** invent those from chat prose — import when `noisegate-sync-2026-11-22/` lands.

## Ops Console / queue (public truth)

- Claude Ops Console = **main demo UI** — replay / policy narrative; **never** CreateSubmission or start a Kaggle gate ([Ops-Console wiki](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Ops-Console)).
- Climb bridge = read-only `docs/scoreboard.json` via `CMU_AGENTIC_AI_ROOT`.
- Factory wakes use loop v2 (`plan.py`, `history.log`, KEPT14, z-gate). Submit law: **1 / UTC day** + Submit-Policy bars.

## Remaining HITL before Dec 2 23:59 UTC

Human-only (no console auto-click):

1. **Confirm / HOLD V22** — second KEPT14 pair (J1); z-gate logged before any submit slot.
2. **CreateSubmission** — at most one per UTC day after bars pass; human clicks on authenticated Cowork/Kaggle session.
3. **V24 (if screened)** — tool-layer read-budget hypothesis; still one-change + pre-gate discipline; human approve for any full gate / submit.
4. **Failed-run recovery / overrides** — audited (e.g. past V20-style overrides).
5. **Beta / GA tags** — SemVer cuts stay human; no silent GA.

## Limitations (say out loud)

- Kaggle ADK host owns the outer ReAct loop — local `supervisor/` guard node does not intercept mid-run on Kaggle.
- Prompt-only deadlines failed (V17); tool-layer levers must be proven on the host or as zip-safe config.
- Local gate ≠ leaderboard; noise band **7.33 ± 2.5** / 30; single-run luck is HOLD.
- Missing sync bundles mean Checkpoint 6.1 + SWE-bench pregate are **not** in this PR.

## Local verification (this VM, 2026-11-25)

```text
CI-equivalent: pytest -q --ignore=tests/test_supervisor.py --ignore=tests/test_sandbox.py
→ 120 passed, 1 skipped

Full (incl. supervisor graph): pytest -q
→ 136 passed, 6 skipped
```

`ruff check .` reports many pre-existing E501 hits on `main`; CI does not gate on ruff today.
