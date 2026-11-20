# Architecture

NoiseGate separates **deterministic factory governance** from the **offline Gemma 4 ReAct coding agent**, with humans on the Ops Console for costly steps. Confusing the bands is the fastest way to mis-read the project.

## Figure 1 — Three bands

```mermaid
flowchart TB
  subgraph L1["Layer 1 — Autonomous Factory · Claude runbook 4×/week"]
    direction LR
    P[Patch<br/>1 delta + SHA-256] --> E[Eval<br/>30-task paired gate]
    E --> W[Watchdog<br/>failures + GPU]
    W --> G[Submit Governor<br/>noise gate · 1/wk slot]
  end

  subgraph L2["Layer 2 — Product · Gemma 4 ReAct · offline 4× L4"]
    T[Shell · Read · Edit · Code-Graph]
    C["≤28 calls · ≤480s · fixed seed · V8–V23"]
  end

  subgraph Ops["State & Human Ops Console"]
    S[State file + event ledger]
    H[Replay · approval gate]
  end

  E -->|runs candidates| L2
  W -.->|observes| L2
  G -->|HITL approve| Ops
  L2 <--> Ops
```

| Band | What it does |
|---|---|
| **Factory (4 roles)** | Patch builds baseline + one change (SHA-256). Eval runs the 30-task paired gate. Watchdog classifies failures and tracks GPU. Submit Governor applies the noise gate and guards the weekly slot. |
| **Product** | Gemma 4 ReAct: reason → tool (shell / read / edit / code-graph) → observe → repeat until patch. Hard caps: ≤28 calls, ≤480s/task, fixed seed. Configs versioned V8–V23. |
| **Ops Console** | State file + append-only event ledger; React Ops Console with replay and approval. **Never** CreateSubmission from the console. |

| | **Product** | **Factory** |
|---|---|---|
| Model | `gemma-4-31b-it` (fixed by competition rules) | Claude scheduled runbook / Project |
| Artifact | ADK config → `submission.zip` | Candidates = base + exactly one change |
| Evaluation | Hidden tests → public/private LB | Local Eval Gate (30 tasks, paired vs V8) + coded decision rule |
| Human role | — | Cadence, full-gate approve, CreateSubmission, final picks |

Core finding: **the harness matters more than the generator**. The factory’s most useful act has been HOLD.

## One weekly turn

```mermaid
flowchart TB
  Q[Queue item] --> BC[Patch / build-candidate<br/>base + 1 change · SHA]
  BC --> GA[Eval Gate A<br/>screen on 30 tasks]
  GA --> GB[Eval Gate B<br/>leader vs V8]
  GB --> WD{Submit Governor<br/>decision_rule.py}
  WD -->|HOLD| RH[Report to humans]
  WD -->|SUBMIT| CS[Human CreateSubmission<br/>≤ 1 / ISO week]
  CS --> Wait[~1.5 days scoring]
  Wait --> RS[record-score + ledger]
  RS -->|LB ≥ best| NB[New base]
```

Cadence (UTC):

```mermaid
flowchart LR
  Sat[Sat: build + Gate A] --> Sun[Sun: Gate B vs V8]
  Sun --> Mon{Mon: weekly-decision}
  Mon -->|HOLD| Ops[Status-only wakes]
  Mon -->|SUBMIT| Hitl[Human CreateSubmission]
  Hitl --> Wait[~1.5d scoring]
  Wait --> Rec[record-score + CSV]
```

Decision logic lives in code (`harness/decision_rule.py`), not free-form chat. Trajectory parsing and evaluators E1–E9 feed the gate; persistent memory is the ledger + `results/`.

## Product ReAct loop (ADK)

```mermaid
flowchart LR
  Issue[Issue + repo] --> Agent[ADK ReAct agent]
  Agent --> Tools[Harness tools]
  Tools --> WS[Workspace]
  Agent --> Policy{Allow / Block}
  Policy -->|ALLOW source edit| Tools
  Policy -->|BLOCK tests/ or bad shell| Trace[Trace + refuse]
  Agent --> Submit[submit_patch]
  Submit --> Tests[Hidden / maintainer tests]
```

## Figure 2 energy — noise band and telemetry

Numbers below are from the capstone evaluation writeup (gate through mid-November 2026). Not a live leaderboard scrape.

### A. Paired gate in-budget solves vs V8 noise band

V8 mean **7.33** in-budget / 30 · empirical noise ~**±2.5** tasks (three repeats: 8, 6, 8).

```mermaid
flowchart LR
  subgraph Band["V8 noise band ~±2.5 around 7.33"]
    V8[V8 base 7.33]
  end
  V21[V21 6.0] -.-> Band
  V18[V18 7.0] -.-> Band
  V15[V15 8.5] -.-> Band
  V22[V22 9.0] -.-> Band
  V11[V11 10.0] -.-> Band
```

| Candidate | In-budget / 30 | Notes |
|---|---|---|
| V8 (base) | 7.33 (8, 6, 8) | Noise calibration |
| V11 | 10.0 (1 run) | Looked better locally → LB **0.15** |
| V15 (public 0.22 copy) | 8.5 (7, 10) | LB **0.17** — board noise |
| V18 | 7.0 | HOLD |
| V21 | 6.0 | HOLD |
| V22 | 9.0 | HOLD pending second run |

### B. Trajectory telemetry (N = 390 gate runs)

| Signal | Value | Takeaway |
|---|---|---|
| Median first edit | call **16 / 28** (~57% budget spent reading) | Agent reads too long |
| Out-of-budget | **243 / 390 (62.3%)** | Cap bites late |
| Wrong fix | **32%** | Dominant failure mode |
| Empty patch | **21%** | Second mode |
| Prompt-only “edit by call 20” (V17) | Ignored | Deadline must be **tool-layer**, not prompt-only |

```mermaid
flowchart LR
  Read[Read loop calls 1–16] --> Edit[Edit / verify 17–28]
  Edit --> Out{Budget?}
  Out -->|62.3% overrun| Fail[Wrong fix 32% · empty 21%]
  Out -->|in budget| Ok[Scored / other]
```

## Table 2 — Governance tiers

| Control tier | Operational action | Authorization & audit |
|---|---|---|
| **Autonomous** | Static checks, candidate packaging, 3-hour screen on 9 contested tasks | Runs on schedule; logged in append-only ledger |
| **Automated reliability cutoff** | Early stop when projected overruns fail hard check | Deterministic watchdog (~3.3 GPU-h saved on V18 replay) |
| **HITL gate** | Full 10-hour 30-task gate, Kaggle submission, failed recovery | Explicit human approval; overrides audited (e.g. V20) |
| **Hard standing guardrails** | Duplicate-hash resubmit, post-deadline runs, deleting notebooks/submissions | Forbidden by policy; final submission human-reserved |

Streamlit `:8765` and the React Ops Console may query / replay / approve ledger writes — they **must not** CreateSubmission or start a Kaggle gate on their own.

## Repository layout (who owns what)

| Path | Owner |
|---|---|
| `product/` | Product configs, candidates table, zip builder |
| `harness/` | Gate math, trajectory parse, eval notebook notes |
| `factory/` | Runbook, Project instructions, Skills |
| `factory_console/` | Local query/demo UI (does not replace Claude for Kaggle login) |
| `supervisor/` + `guardrails/` + `agentops/` | Course supervisor slice (LangGraph); **not** in the Kaggle zip |
| `evals/` | Adversarial safety cases |
| `results/` | Factory bookkeeping (gate CSV + leaderboard CSV) |

## Climb bridge (#4 merged)

Sibling climb tooling and the live publicScore source of truth live in `cmu-agentic-ai` (`docs/scoreboard.json`). NoiseGate’s `results/leaderboard.csv` is factory bookkeeping and can disagree until operators reconcile.

```mermaid
flowchart LR
  subgraph CMU["cmu-agentic-ai — climb SoT"]
    SB[docs/scoreboard.json]
    Tips[submission/ tip packages]
  end

  subgraph NG["NoiseGate factory console"]
    CSV[results/leaderboard.csv]
    Cons[Streamlit tools<br/>climb_scoreboard]
  end

  SB -->|read-only via CMU_AGENTIC_AI_ROOT| Cons
  Cons -->|score_mismatch flag| CSV
  Tips -.->|ADK zip configs| Prod[product/]
```

With [#4](https://github.com/khaosans/noisegate-gemma4-factory/pull/4) and Ollama [#3](https://github.com/khaosans/noisegate-gemma4-factory/pull/3) on `main`:

- Console tools `climb_scoreboard` / `kaggle_submissions_snapshot` read via `CMU_AGENTIC_AI_ROOT`
- `factory_status` can report `score_mismatch`
- Still **no** CreateSubmission, gate-start, or auto CSV overwrite from Streamlit

## What ships where

| Surface | Ships |
|---|---|
| Kaggle competition | Product ADK zip only |
| Demo | Ops Console + Streamlit `:8765` + this wiki |
| Course evidence (non-zip) | LangGraph supervisor, guardrails, AgentOps, safety eval |

See also: [[Claude-Cowork-Loop]], [[Local-And-Streamlit]], [[Requirements-Compliance]].
