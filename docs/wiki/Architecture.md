# Architecture

NoiseGate separates **deterministic factory governance** from the **offline Gemma 4 ReAct coding agent**, with humans on the Ops Console for costly steps. Confusing the bands is the fastest way to mis-read the project.

The product targets issue-fixing under a fixed competition harness (SWE-bench-style tasks; Kaggle ADK host). Behavior is a ReAct loop: reason → tool → observe → patch.

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

  Key["Key: green Factory · amber Product · blue Ops"]

  E -->|runs candidates| L2
  W -.->|observes| L2
  G -->|HITL approve| Ops
  L2 <--> Ops
  G ~~~ Key

  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  classDef ops fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  class P,E,W,G factory
  class T,C product
  class S,H ops
  style L1 fill:#ECFDF5,stroke:#059669,color:#065F46
  style L2 fill:#FFF7ED,stroke:#EA580C,color:#9A3412
  style Ops fill:#F0F9FF,stroke:#0284C7,color:#075985
  style Key fill:#FAFAF9,stroke:#A8A29E,color:#44403C
```

*Insight.* Layer 1 decides **whether to spend GPU / the weekly slot**; Layer 2 only solves tasks. Ops is audit + HITL — never CreateSubmission.

| Band | What it does |
|---|---|
| **Factory (4 roles)** | Patch = base + one change (SHA-256). Eval = 30-task paired gate. Watchdog = failures + GPU. Submit Governor = noise gate + weekly slot. |
| **Product** | Gemma 4 ReAct under ≤28 calls / ≤480s / fixed seed. Configs V8–V23. |
| **Ops Console** | State file + append-only ledger; replay + approval. **Never** CreateSubmission. |

| | **Product** | **Factory** |
|---|---|---|
| Model | `gemma-4-31b-it` (fixed) | Claude scheduled runbook |
| Artifact | ADK → `submission.zip` | Base + exactly one change |
| Evaluation | Hidden tests → LB | Paired gate vs V8 + coded decision rule |
| Human role | — | Cadence, full-gate approve, CreateSubmission, final picks |

Core finding: **the harness matters more than the generator.** The factory’s most useful act has been HOLD.

## One weekly turn

```mermaid
flowchart TB
  Q[Queue item] --> BC[Patch / build-candidate<br/>base + 1 change · SHA]
  BC --> GA[Eval Gate A<br/>screen two on 30 tasks]
  GA --> GB[Eval Gate B<br/>leader vs V8 · else next pair]
  GB --> WD{Submit Governor<br/>decision_rule.py}
  WD -->|HOLD| RH[Report to humans]
  WD -->|SUBMIT| CS[Human CreateSubmission<br/>≤ 1 / ISO week]
  CS --> Wait[~1.5 days scoring]
  Wait --> RS[record-score + ledger]
  RS -->|LB ≥ best| NB[New base]

  Key["Key: green factory · gray HOLD · red CreateSubmission"]
  NB ~~~ Key

  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  classDef hold fill:#F3F4F6,stroke:#6B7280,color:#374151
  class Q,BC,GA,GB,WD,RS,NB,Wait factory
  class CS hitl
  class RH hold
  style Key fill:#FAFAF9,stroke:#A8A29E,color:#44403C
```

*Insight.* Run A screens cheaply; Run B pairs a leader vs V8 (or the next pair). `decision_rule.py` makes HOLD/SUBMIT reproducible — not chat.

If **both** Run A candidates sit below V8’s mean, Run B screens the **next two** queue items instead of `[V8, leader]` (runbook; single-run bar applies).

```mermaid
flowchart LR
  Sat[Sat: build + Gate A] --> Sun[Sun: Gate B<br/>V8 or next pair]
  Sun --> Mon{Mon: weekly-decision}
  Mon -->|HOLD| Ops[Status-only wakes]
  Mon -->|SUBMIT| Hitl[Human CreateSubmission]
  Hitl --> Wait[~1.5d scoring]
  Wait --> Rec[record-score + CSV]

  Key["Key: green cadence · gray HOLD · red CreateSubmission"]
  Rec ~~~ Key

  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  classDef hold fill:#F3F4F6,stroke:#6B7280,color:#374151
  class Sat,Sun,Mon,Wait,Rec factory
  class Ops hold
  class Hitl hitl
  style Key fill:#FAFAF9,stroke:#A8A29E,color:#44403C
```

*Insight.* Status-only wakes refresh scores without inventing submits; ~1.5d scoring lag → ≤1 gated submit / ISO week.

## Product ReAct loop (ADK zip)

Graded path only — what ships inside `submission.zip`:

```mermaid
flowchart LR
  Issue[Issue + repo] --> Agent[ADK ReAct agent]
  Agent --> Tools[Shell · Read · Edit · Code-Graph]
  Tools --> WS[Workspace]
  Agent --> Submit[submit_patch]
  Submit --> Tests[Hidden / maintainer tests]

  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  class Issue,Agent,Tools,WS,Submit,Tests product
```

*Insight.* Graded contract: one ADK agent → tools → patch → hidden tests. Allow/Block + escalate live in `supervisor/` / `guardrails/` — **not** in the zip. [[Requirements-Compliance]].

## Figure 2 — Noise band and telemetry

Numbers from the capstone evaluation (gate through mid-November 2026). Not a live leaderboard scrape.

### A. Paired gate vs V8 noise band

V8 mean **7.33** in-budget / 30 · empirical noise ~**±2.5** (repeats 8, 6, 8).

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

  Key["Key: yellow noise · gray HOLD · red false+"]
  V11 ~~~ Key

  classDef noise fill:#FEF9C3,stroke:#A16207,color:#713F12
  classDef inside fill:#F3F4F6,stroke:#6B7280,color:#374151
  classDef falsepos fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  class V8 noise
  class V21,V18,V15,V22 inside
  class V11 falsepos
  style Band fill:#FEFCE8,stroke:#CA8A04,color:#713F12
  style Key fill:#FAFAF9,stroke:#A8A29E,color:#44403C
```

*Insight.* In-band = noise, not a ship signal. V11’s local 10 → LB **0.15**; V15 (public 0.22) → **0.17**. The gate is trusted to refuse false promotions.

| Candidate | In-budget / 30 | Notes |
|---|---|---|
| V8 (base) | 7.33 (8, 6, 8) | Noise calibration |
| V11 | 10.0 (1 run) | Local win → LB 0.15 |
| V15 (public 0.22 copy) | 8.5 (7, 10) | LB 0.17 — board noise |
| V18 | 7.0 | HOLD |
| V21 | 6.0 | HOLD |
| V22 | 9.0 | HOLD pending second run |

### B. Trajectory telemetry (N = 390)

```mermaid
flowchart LR
  Read[Read loop calls 1–16] --> Edit[Edit / verify 17–28]
  Edit --> Out{Budget?}
  Out -->|62.3% overrun| Fail[Wrong fix 32% · empty 21%]
  Out -->|in budget| Ok[Scored / other]

  Key["Key: amber phases · red fail · green ok"]
  Ok ~~~ Key

  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  classDef fail fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  classDef ok fill:#D1FAE5,stroke:#047857,color:#064E3B
  class Read,Edit,Out product
  class Fail fail
  class Ok ok
  style Key fill:#FAFAF9,stroke:#A8A29E,color:#44403C
```

*Insight.* Median first edit at call **16/28** — most budget is reading. Prompt-only deadlines (V17) failed; next lever is a **tool-layer** edit cap.

| Signal | Value | Takeaway |
|---|---|---|
| Median first edit | call **16 / 28** | Read loop too long |
| Out-of-budget | **243 / 390 (62.3%)** | Cap bites late |
| Wrong fix / empty patch | **32% / 21%** | Dominant failure modes |
| Prompt-only deadline (V17) | Ignored | Enforce in tools |

## Table 2 — Governance tiers

| Control tier | Operational action | Authorization & audit |
|---|---|---|
| **Autonomous** | Static checks, packaging, 3-hour screen on 9 contested tasks | Scheduled; logged in ledger |
| **Automated reliability cutoff** | Early stop when projected overruns fail hard check | Deterministic watchdog (~3.3 GPU-h saved on V18 replay) |
| **HITL gate** | Full 10-hour gate, Kaggle submission, failed recovery | Explicit human approval; overrides audited (e.g. V20) |
| **Hard standing guardrails** | Duplicate-hash resubmit, post-deadline runs, deleting notebooks/submissions | Forbidden; final submission human-reserved |

*Insight — why HITL tiers.* Cheap steps automate; expensive or irreversible steps require a person. That is how the factory stays autonomous without gambling the weekly slot or deleting artifacts.

Streamlit `:8765` and the React Ops Console may query / replay / approve ledger writes — they **must not** CreateSubmission or start a Kaggle gate on their own.

## Repository layout

| Path | Owner |
|---|---|
| `product/` | Configs, candidates, zip builder |
| `harness/` | Gate math, trajectory parse |
| `factory/` | Runbook, Skills |
| `factory_console/` | Local query/demo UI |
| `supervisor/` + `guardrails/` + `agentops/` | Course slice — **not** in Kaggle zip |
| `evals/` · `results/` | Safety cases · bookkeeping |

## Climb bridge (#4 merged)

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

  Key["Key: blue climb SoT · green NG CSV · amber product"]
  Prod ~~~ Key

  classDef ops fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  class SB,Tips,Cons ops
  class Prod product
  class CSV factory
  style CMU fill:#F0F9FF,stroke:#0284C7,color:#075985
  style NG fill:#ECFDF5,stroke:#059669,color:#065F46
  style Key fill:#FAFAF9,stroke:#A8A29E,color:#44403C
```

*Insight.* Climb `scoreboard.json` = live publicScore SoT; NG CSV = bookkeeping. Bridge is read-only — no CreateSubmission from Streamlit ([#4](https://github.com/khaosans/noisegate-gemma4-factory/pull/4), [#3](https://github.com/khaosans/noisegate-gemma4-factory/pull/3)).

## What ships where

| Surface | Ships |
|---|---|
| Kaggle | Product ADK zip only |
| Demo | Ops Console + Streamlit `:8765` + this wiki |
| Course evidence (non-zip) | LangGraph supervisor, guardrails, AgentOps |

See also: [[Claude-Cowork-Loop]], [[Local-And-Streamlit]], [[Requirements-Compliance]].

## References

1. Jimenez et al., *SWE-bench* (ICLR 2024) — issue-fixing benchmark lineage.  
2. Yao et al., *ReAct* (ICLR 2023) — product agent loop.  
3. Kaggle & Google DeepMind, *Gemma 4 Developer Agent* (2026) — fixed model, 28 calls, 480s/task.
