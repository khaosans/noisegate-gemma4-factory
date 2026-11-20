# Security

## Reporting

This is a research / class product repo (MIT). For security concerns about this codebase, open a private report to the maintainers via GitHub Security Advisories on this repository, or contact the authors listed in the README. Do **not** file public issues that include credentials or competition secrets.

## What we never commit

- Kaggle credentials, API tokens, Anthropic / cloud keys
- Competition task data, hidden tests, or model weights
- Emeritus / CMU proprietary syllabus text (course IP stays out of this product repo)

## Trust boundaries (factory)

| Surface | May | Must not |
|---------|-----|----------|
| Claude Cowork climb loop | Propose candidates, start gates (authenticated session) | Auto-CreateSubmission without human |
| Claude Ops Console artifact (**main demo UI**) | Demo / paper replay UI | Gate-start, CreateSubmission, inventing scores; treat as demo-only |
| Climb bridge (`CMU_AGENTIC_AI_ROOT`) | Read-only scoreboard / submissions snapshot | Write climb ledger or submit |
| LangGraph `supervisor/` | Local course guardrails / escalate | Ship inside the Kaggle ADK zip |

Least-privilege design for the course tracker’s agent/MCP scopes lives in the sibling repo `cmu-agentic-ai` (`docs/security/`). CreateSubmission there uses a **trusted-client** `confirm=true` flag plus judge SUBMIT — not a separate human UI gate unless the operator enforces one.

## Dependencies

Prefer pinned installs from `requirements*.txt` / `pyproject.toml`. Run `pytest` and `python -m evals.safety.run` before trusting a local supervisor demo.
