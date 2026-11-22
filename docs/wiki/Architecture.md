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

  E -->|runs candidates| L2
  W -.->|observes| L2
  G -->|HITL approve| Ops
  L2 <--> Ops

  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  classDef ops fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  class P,E,W,G factory
  class T,C product
  class S,H ops
  style L1 fill:#ECFDF5,stroke:#059669,color:#065F46
  style L2 fill:#FFF7ED,stroke:#EA580C,color:#9A3412
  style Ops fill:#F0F9FF,stroke:#0284C7,color:#075985
```

*Insight.* Layer 1 decides **whether to spend GPU / a UTC-day submit slot**; Layer 2 only solves tasks. Ops is audit + HITL — never CreateSubmission. Current bars: [[Submit-Policy]].

| Band | What it does |
|---|---|
| **Factory (4 roles)** | Patch = base + one change (SHA-256). Eval = paired / screen gate. Watchdog = failures + GPU. Submit Governor = [[Submit-Policy]] bars + 1/UTC-day. |
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
  WD -->|SUBMIT| CS[Human CreateSubmission<br/>1 / UTC day]
  CS --> Wait[~1.5 days scoring]
  Wait --> RS[record-score + ledger]
  RS -->|LB ≥ best| NB[New base]

  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  classDef hold fill:#F3F4F6,stroke:#6B7280,color:#374151
  class Q,BC,GA,GB,WD,RS,NB,Wait factory
  class CS hitl
  class RH hold
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

  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  classDef hold fill:#F3F4F6,stroke:#6B7280,color:#374151
  class Sat,Sun,Mon,Wait,Rec factory
  class Ops hold
  class Hitl hitl
```

*Insight.* Status-only wakes refresh scores without inventing submits. Host scoring lag (~1.5d) is observation only — submit cadence SoT: [[Submit-Policy]] (**1 / UTC day** + quality bars).

## Record-keeping cadence — before vs after

**Live since 2026-11-20: loop v2.** The Sat/Sun/Mon table is still a useful **work skeleton**. What changed in loop v2 is how wakes **choose work** and how **ledger / gate math** are recorded. Separately (2026-11-21), **submit cadence** dropped homemade weekly caps — see [[Submit-Policy]]. Keep the diagrams below when explaining the factory ledger — v1 is how we used to run; v2 is how we record now.

### Before — loop v1 (calendar-driven)

```mermaid
flowchart TB
  subgraph Cal["Loop v1 · calendar driver · retired 2026-11-20"]
    direction LR
    Sat1[Sat: build + Gate A] --> Sun1[Sun: Gate B]
    Sun1 --> Mon1[Mon: weekly-decision]
    Mon1 --> St1[Other wakes: status / record-score]
  end

  subgraph Rec1["Record-keeping v1"]
    direction LR
    G30["30-task paired gate"] --> Noise["decision_rule<br/>noise band ~+/-2.5"]
    Noise --> CSV1["results CSV + eval-results.md"]
  end

  Cal --> Rec1
  Rec1 --> Hitl1["Human CreateSubmission"]

  classDef retired fill:#F3F4F6,stroke:#6B7280,color:#374151
  classDef record fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  class Sat1,Sun1,Mon1,St1,G30,Noise retired
  class CSV1 record
  class Hitl1 hitl
  style Cal fill:#F9FAFB,stroke:#9CA3AF,color:#374151
  style Rec1 fill:#F0F9FF,stroke:#0284C7,color:#075985
```

*Insight.* v1: the **clock** decided the next action. Gate math and narrative lived almost entirely in `results/`.

### After — loop v2 (event-driven + wake ledger)

```mermaid
flowchart TB
  subgraph Drive["Loop v2 · event driver · live"]
    direction LR
    Plan["plan.py next"] --> Act["START · WAIT · PARSE<br/>DEFER · IDLE · SKIP"]
    Act --> Jobs["jobs array · KEPT14 · z-gate"]
  end

  subgraph Rec2["Record-keeping v2"]
    direction LR
    State["state.json key v2<br/>+ state.v1.json rollback"] --> Led["history.log append-only"]
    Led --> CSV2["results CSV + eval-results.md"]
  end

  subgraph Keep["Human + host limits"]
    direction LR
    Skel["Sat / Sun / Mon<br/>work skeleton"] --> Hitl2["Human CreateSubmission<br/>1 / UTC day"]
  end

  Drive --> Rec2
  Jobs -.->|screens / confirms| Keep
  CSV2 -->|LB ge best| Base["New base"]

  classDef live fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef record fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  classDef hold fill:#F3F4F6,stroke:#6B7280,color:#374151
  class Plan,Act,Jobs,Base live
  class State,Led,CSV2 record
  class Hitl2 hitl
  class Skel hold
  style Drive fill:#ECFDF5,stroke:#059669,color:#065F46
  style Rec2 fill:#F0F9FF,stroke:#0284C7,color:#075985
  style Keep fill:#FEF2F2,stroke:#DC2626,color:#7F1D1D
```

*Insight.* v2: **jobs + `plan.py`** decide the next action; every wake appends `history.log`. Gate decisions use **KEPT14 + z-gate**. CreateSubmission stays human; **slot math** is host **1 / UTC day** + [[Submit-Policy]] bars (not the old ISO-week factory caps). Schemas: [`factory/state-and-artifacts.md`](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/factory/state-and-artifacts.md) · climb narrative [[Claude-Cowork-Loop]].

| | **v1 (before)** | **v2 (after · live)** |
|---|---|---|
| What picks work | Fixed Sat / Sun / Mon / status calendar | `plan.py next` over `jobs[]` |
| Gate set | 30-task paired runs | **KEPT14** (V8 paired every run) |
| Ship rule | Noise-band `decision_rule` | **z-gate** + hard checks; see also [[Submit-Policy]] screens |
| Ledger | `results/` CSVs + `eval-results.md` | Same **plus** `history.log` + `state.json` `v2` |
| Human | CreateSubmission · base · policy | **Same** (consoles never submit; **1 / UTC day**) |

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

## Gemma agent + Eval Gate harness

How a candidate is measured before any weekly submit. Two bands: the **product** ReAct agent under the fixed competition contract, and the **harness** that turns notebook logs into HOLD/SUBMIT.

```mermaid
flowchart TB
  subgraph Product["Product · Gemma 4 ADK ReAct"]
    direction LR
    Cfg[product/superagent<br/>prompts · agent.yaml] --> Zip[build_submission.py<br/>submission.zip]
    Zip --> Run[Kaggle / Eval Gate host<br/>gemma-4-31b-it]
    Run --> Loop[ReAct: reason → tool → observe]
    Loop --> Cap["Budget: ≤28 calls · ≤480s"]
    Cap --> Patch[submit_patch]
  end

  subgraph Harness["Harness · local gate math"]
    direction LR
    Log[Gate notebook Score lines] --> Parse[trajectory.parse_log]
    Parse --> Evals[evaluators E1–E9]
    Evals --> Sum[RunSummary]
    Sum --> Dec{decision_rule.decide}
    Dec -->|pass| Prop[Propose submit]
    Dec -->|fail| Hold[HOLD]
  end

  Patch -.->|same config on 30-task gate| Log
  Prop --> Hitl[Human CreateSubmission · 1 / UTC day]

  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  classDef harness fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  class Cfg,Zip,Run,Loop,Cap,Patch product
  class Log,Parse,Evals,Sum,Dec,Prop,Hold harness
  class Hitl hitl
  style Product fill:#FFF7ED,stroke:#EA580C,color:#9A3412
  style Harness fill:#ECFDF5,stroke:#059669,color:#065F46
```

*Insight.* The ADK zip is the **generator**; `harness/` is the **evaluator**. Factory Skills start the gate notebook and append `results/`; `decide()` never invents a score. V8 baseline history loads from `results/gate_runs.csv`.

| Stage | Code | Output |
|---|---|---|
| Build candidate | `product/build_submission.py`, Skills `build-candidate` | Versioned zip + SHA-256 |
| Run paired gate | Kaggle Eval Gate notebook | Per-task `Score` lines |
| Parse / score | `harness/trajectory.py`, `evaluators.py` | Typed rows · E1–E9 |
| Decide | `harness/decision_rule.py` | HOLD / SUBMIT tier · Δ vs V8 |

## LangChain / LangGraph local stack

Course evidence only — **not** in the Kaggle zip. LangChain supplies chat messages; LangGraph owns control flow; `guardrails/` is plain Python with no LangChain imports (Decision 007).

```mermaid
flowchart TB
  subgraph LC["LangChain · model I/O"]
    Msg[langchain_core messages] --> Chat[BaseChatModel<br/>Gemma / local tag]
  end

  subgraph LG["LangGraph · control flow"]
    direction LR
    Start[START] --> Intake[intake]
    Intake --> Agent[agent<br/>one JSON tool call]
    Agent --> Guard[guard]
    Guard -->|allow| Exec[execute]
    Guard -->|block / boundary| Esc[escalate]
    Exec --> Agent
    Exec -->|submit_patch| Verify[verify]
    Verify --> Fin[finalize]
    Esc --> Fin
    Fin --> EndNode[END]
  end

  subgraph GR["guardrails/ · policy in code"]
    Pol[Policy · allow-list tools] --> Bud[Budget 28 calls · 8 min]
    Bud --> PatchChk[Patch / path checks]
    PatchChk --> Shell[Shell allow-list + sandbox]
  end

  subgraph AO["agentops/ · observability"]
    JSONL[JSONL run log] --> Metrics[Checkpoint metrics]
    Metrics --> LS[LangSmith when enabled]
  end

  Chat --> Agent
  Guard --> Pol
  Exec --> Shell
  Agent --> JSONL
  Esc -.->|hitl=True interrupt| Human[Human resume]

  classDef lc fill:#E0E7FF,stroke:#4338CA,color:#312E81
  classDef lg fill:#F3E8FF,stroke:#7E22CE,color:#581C87
  classDef gr fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef ao fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  class Msg,Chat lc
  class Start,Intake,Agent,Guard,Exec,Verify,Esc,Fin,EndNode lg
  class Pol,Bud,PatchChk,Shell gr
  class JSONL,Metrics,LS ao
  class Human hitl
  style LC fill:#EEF2FF,stroke:#4F46E5,color:#312E81
  style LG fill:#FAF5FF,stroke:#9333EA,color:#581C87
  style GR fill:#ECFDF5,stroke:#059669,color:#065F46
  style AO fill:#F0F9FF,stroke:#0284C7,color:#075985
```

*Insight.* The model **proposes**; code **decides**. Budgets and path policy run in `guard` / `execute`, including call counters injected into tool results (the lever prompt-only V17 lacked). Safety evals: `evals/safety` · 55/55 adversarial blocked, 0/29 false positives.

| Package | Role |
|---|---|
| `supervisor/` | LangGraph `StateGraph` — intake → agent → guard → execute → verify / escalate |
| `guardrails/` | Policy, budgets, patch checks, shell allow-list — no LangChain imports |
| `agentops/` | JSONL traces + checkpoint metrics; optional LangSmith |
| `evals/safety/` | Adversarial + benign twins through the full graph |

Ship contrast: [[Requirements-Compliance]] (ADK zip vs this stack).

## Policy vs. Agent Runtimes (Why This Stack)

One plain-Python governance layer; three runtimes. The model **proposes**; code **decides** — but *where* that code can sit differs by host.

```mermaid
flowchart TB
  subgraph Policy["Shared plain-Python governance"]
    direction LR
    G[guardrails/] --> D[harness/decision_rule.py]
    D --> P[factory/plan.py]
    Note["The model proposes · code decides"]
  end

  subgraph Product["Product · Kaggle ADK host · submission.zip"]
    ADK["Single-agent ReAct<br/>gemma-4-31b-it · 4x L4"]
    Cap["Budget: max 28 calls · max 480s · fixed seed"]
    Own["Host owns outer loop<br/>supervisor cannot intercept mid-run"]
    ADK --> Cap --> Own
  end

  subgraph Local["Local reference · LangGraph · supervisor/"]
    Graph["intake to agent to guard to execute<br/>to verify / escalate to finalize"]
    Hook["In-loop interception · call counters<br/>hitl interrupt · evals/safety"]
    Graph --> Hook
  end

  subgraph Factory["Factory · event-driven wakes · factory/"]
    Wake["plan.py + state.json v2 + history.log"]
    Hitl["Claude runbook wakes<br/>CreateSubmission 1 / UTC day"]
    Wake --> Hitl
  end

  Policy --> Product
  Policy --> Local
  Policy --> Factory

  classDef policy fill:#D1FAE5,stroke:#047857,color:#064E3B
  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  classDef lg fill:#F3E8FF,stroke:#7E22CE,color:#581C87
  classDef factory fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  classDef hitl fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  class G,D,P,Note policy
  class ADK,Cap,Own product
  class Graph,Hook lg
  class Wake factory
  class Hitl hitl
  style Policy fill:#ECFDF5,stroke:#059669,color:#065F46
  style Product fill:#FFF7ED,stroke:#EA580C,color:#9A3412
  style Local fill:#FAF5FF,stroke:#9333EA,color:#581C87
  style Factory fill:#F0F9FF,stroke:#0284C7,color:#075985
```

*Insight.* On Kaggle the outer ReAct loop is **host-owned**, so prompt-only deadlines (V17) were ignored and the next lever is a **tool-layer** budget cue. LangGraph proves in-loop interception locally without pretending it ships in the zip. The factory stays a file-backed wake loop with human CreateSubmission ([[Submit-Policy]]).

| Choice | Why |
|---|---|
| **Single-agent ADK + plain Python** (not CrewAI) | Multi-agent role chatter burns the **28-call / 480s** budget (median first edit already **16/28**, N=390) and breaks the one-ADK-zip contract. |
| **LangGraph in `supervisor/` only** | Live factory stays lightweight (`plan.py` + `decision_rule.py`). The standalone graph proves stateful orchestration + code-enforced guardrails for course evidence — not as the Kaggle supervisor. |
| **Not A2A; MCP optional later** | Bands talk through deterministic ledgers (`state.json`, `history.log`, CSVs) + HITL — not real-time agent negotiation. MCP could later standardize local tool schemas without adding an orchestration tax. |

Safety proof on the local graph: **55/55** adversarial blocked, **0/29** false positives (`evals/safety`).

## Figure 2 — Noise band and telemetry

Numbers from the capstone evaluation (gate through mid-November 2026). Not a live leaderboard scrape. Full scoring axes + failure taxonomy: [[Trajectory-Eval-Rubric]].

### A. Paired gate vs V8 noise band

![NoiseGate Evaluation Band](assets/gate_noise_band.png)

V8 mean **7.33** in-budget / 30 · empirical noise ~**±2.5** (repeats 8, 6, 8). In-band = **HOLD**. Full caption, 4-tier rubric, and failure taxonomy: [[Trajectory-Eval-Rubric]].

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

  classDef noise fill:#FEF9C3,stroke:#A16207,color:#713F12
  classDef inside fill:#F3F4F6,stroke:#6B7280,color:#374151
  classDef falsepos fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  class V8 noise
  class V21,V18,V15,V22 inside
  class V11 falsepos
  style Band fill:#FEFCE8,stroke:#CA8A04,color:#713F12
```

*Insight.* In-band = noise, not a ship signal. V11’s local 10 → LB **0.15**; V15 (public 0.22) → **0.17**. The gate is trusted to refuse false promotions.

| Candidate | In-budget / 30 | Notes |
|---|---|---|
| V8 (base) | 7.33 (8, 6, 8) | Noise calibration |
| V11 | 10.0 (1 run) | Local win → LB 0.15 |
| V15 (public 0.22 copy) | 8.5 (7, 10) | LB 0.17 — board noise |
| V18 | 7.0 | HOLD |
| V21 | 6.0 | HOLD |
| V22 | 9.0 | CONFIRM — second paired run pending |

**Calibration tally** (local direction vs LB; from `results/README.md`):

| Point | Agree with LB? |
|-------|----------------|
| V11 | **No** (local better, LB worse) |
| V12 | **Yes** |
| V15 | Inconclusive (within noise) |

### B. Trajectory telemetry (N = 390)

```mermaid
flowchart LR
  Read[Read loop calls 1–16] --> Edit[Edit / verify 17–28]
  Edit --> Out{Budget?}
  Out -->|62.3% overrun| Fail[Wrong fix 32% · empty 21%]
  Out -->|in budget| Ok[Scored / other]

  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  classDef fail fill:#FEE2E2,stroke:#B91C1C,color:#7F1D1D
  classDef ok fill:#D1FAE5,stroke:#047857,color:#064E3B
  class Read,Edit,Out product
  class Fail fail
  class Ok ok
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

*Insight — why HITL tiers.* Cheap steps automate; expensive or irreversible steps require a person. That is how the factory stays autonomous without gambling a CreateSubmission slot or deleting artifacts.

The Claude Ops Console (**main** demo UI) may illustrate query / replay / approval — it **must not** CreateSubmission or start a Kaggle gate. See [[Ops-Console]].

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

  classDef ops fill:#E0F2FE,stroke:#0369A1,color:#0C4A6E
  classDef product fill:#FFEDD5,stroke:#C2410C,color:#7C2D12
  classDef factory fill:#D1FAE5,stroke:#047857,color:#064E3B
  class SB,Tips,Cons ops
  class Prod product
  class CSV factory
  style CMU fill:#F0F9FF,stroke:#0284C7,color:#075985
  style NG fill:#ECFDF5,stroke:#059669,color:#065F46
```

*Insight.* Climb `scoreboard.json` = live publicScore SoT; NG CSV = bookkeeping. Bridge is read-only — no CreateSubmission from Streamlit ([#4](https://github.com/khaosans/noisegate-gemma4-factory/pull/4), [#3](https://github.com/khaosans/noisegate-gemma4-factory/pull/3)).

## What ships where

| Surface | Ships |
|---|---|
| Kaggle | Product ADK zip only (**Product runtime** above) |
| Demo | Claude Ops Console (**main**) · this wiki |
| Course evidence (non-zip) | LangGraph supervisor, guardrails, AgentOps (**Local reference runtime**) |
| Climb ops | Factory wake loop + [[Submit-Policy]] (**Factory runtime**) |

Policy vs runtimes framing: [Policy vs. Agent Runtimes (Why This Stack)](#policy-vs-agent-runtimes-why-this-stack). See also: [[Claude-Cowork-Loop]], [[Ops-Console]], [[Requirements-Compliance]].

## References

1. Jimenez et al., *SWE-bench* (ICLR 2024) — issue-fixing benchmark lineage.  
2. Yao et al., *ReAct* (ICLR 2023) — product agent loop.  
3. Kaggle & Google DeepMind, *Gemma 4 Developer Agent* (2026) — fixed model, 28 calls, 480s/task.
