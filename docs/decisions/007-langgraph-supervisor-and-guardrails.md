# 007. A LangGraph supervisor that enforces guardrails in code

**Status:** Accepted (2026-11-11). Scope addition for Capstone Checkpoint 6.1.

## Context
Checkpoint 6.1 (Safety and Intervention Plan) commits to an allow-list of schema-validated
tools, workspace-only paths, hard budgets (28 calls, 8 min), a breaker after three failed
edits, output checks on every patch, escalation to a human, and measured safety metrics.

The Kaggle submission cannot carry any of that: it is a prompt plus `agent.yaml`, run by the
competition's own runtime. Decision 006 showed why that matters: a deadline stated only in
the prompt was ignored (8 of V17's 9 empty runs still edited at call 29–30 or never).

## Decision
Add a local runtime next to the product, built on LangGraph 1.x:

| Package | Role |
|---|---|
| `guardrails/` | Plain-Python policy, budgets, patch checks, untrusted-text handling. No LangChain imports. |
| `supervisor/` | LangGraph `StateGraph`: intake → agent → guard → execute → verify, plus escalate and finalize. Gemma proposes one JSON tool call per step; code decides whether it runs. |
| `agentops/` | JSONL run logs, the seven checkpoint metrics, and a query CLI. LangSmith tracing when enabled. |
| `evals/safety/` | Six adversarial prompt-injection cases and their benign twins, played through the full graph. |

LangChain is used only for the chat-model interface and messages. LangGraph owns control flow,
routing, and the human interrupt.

## What this does and does not change
- The Kaggle submission and the weekly factory loop are unchanged. The supervisor is where the
  guardrails are enforced and tested, and where decision 006's "budget in tool results" now
  runs (`[call 9 of 28 | 300 s left]` heads every tool result).
- Shell commands pass an allow-list (`guardrails/shell.py`): a short set of commands, paths
  inside the workspace only, and no `bash -c`, command substitution, subshells or variables.
  The first version used a list of forbidden patterns; 16 of 16 simple disguises
  (`/usr/bin/curl`, `bash -c '...'`, `git -C . push`, `/bin/rm`) got through it, so it was replaced.
- The allow-list cannot contain `python -c` or the tests themselves, which run code the model
  can edit. The OS sandbox does that. On macOS the default is `seatbelt` (`sandbox-exec`): no
  network, no writes outside the task's temporary folder, no reads under `/Users` or `/Volumes`
  except the Python installation. `NOISEGATE_SANDBOX=docker` runs commands with `--network none`
  and only the workspace mounted; it is untested here (no Docker daemon on the dev machine).
  On Linux without Docker the mode is `local` (no OS isolation), and `python -m supervisor`
  refuses to drive a live model in it unless `--unsafe-no-sandbox` is passed.
- Seatbelt still allows reads outside `/Users` and `/Volumes` (for example `/etc`), and
  `sandbox-exec` is deprecated by Apple although it still ships. Docker is the stricter option.
- Escalations pause for a human only with `hitl=True` (a LangGraph interrupt held in an
  in-memory checkpointer, so resume in the same process).

## Consequences
- Guardrail claims in the checkpoint are now backed by tests: 80 policy/budget/patch tests, 6 sandbox tests,
  15 graph tests (golden cases G1–G5), and the safety eval (G6–G17).
- Two new dependencies (`langgraph`, `langchain-core`). The harness tests still run without them.
- The adversarial cases are synthetic and the fixture repo is tiny, so the safety numbers prove
  the policy, not Gemma's behaviour. A live run with Gemma on the same cases is the next step.
