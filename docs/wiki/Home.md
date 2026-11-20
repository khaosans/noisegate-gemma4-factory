# NoiseGate Gemma 4 Factory

> Preferred viewer: this [GitHub Wiki](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Home). Editors sync from in-repo `docs/wiki/`.

An autonomous **build → evaluate → submit** loop that separates real agent improvements from benchmark noise.

The public notebook that shows **0.22** scored **0.17** when we submitted it. Baseline **V8** fluctuates **8 / 6 / 8** on the same 30 tasks. One planned submit / week + ~30 GPU hours → trusting a single score burns luck.

| | |
|---|---|
| Authors | Souriya Khaosanga · Adil Shamim |
| Competition | [Gemma 4 Developer Agent](https://www.kaggle.com/competitions/gemma-4-developer-agent) · deadline 2026-12-02 |
| Best public (base) | **0.18** (V8) |
| Repo | [noisegate-gemma4-factory](https://github.com/khaosans/noisegate-gemma4-factory) |
| Video | https://youtu.be/-EiKv_MafOY |
| Ops Console (**main UI**) | [artifact](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW) · docs [[Ops-Console]] |

**Score SoT:** factory base here is **V8 @ 0.18**. Sibling [`cmu-agentic-ai`](https://github.com/khaosans/cmu-agentic-ai) climb tips use `docs/scoreboard.json` (may differ, e.g. tip best **0.10**) — not the same artifact ledger.

## Architecture at a glance

Factory governance above a Gemma 4 ReAct product; humans on the Ops Console for costly steps. Console never CreateSubmission.

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

*Insight.* The surface that matters is the **noise gate** between Eval and Submit — gains inside V8’s ±2.5 band HOLD. [[Architecture]].

## Demo in under a minute

1. Open the [[Ops-Console]] Claude artifact (**main UI**).
2. Show a HOLD above the V8 noise band (V18 / V21 / V17).
3. Climb login path = Claude Skills — not the console for CreateSubmission.

Talk track: [[Demo-Script]].

## Pages

| Page | Purpose |
|---|---|
| [[Method-Card]] | One-page academic method (problem → gate → evidence) |
| [[Architecture]] | Figure 1 · weekly turn · noise/telemetry · HITL tiers |
| [[Ops-Console]] | **Main** Claude Agent Ops Console (screens + deny list) vs Cowork |
| [[Claude-Cowork-Loop]] | Schedule + Skills |
| [[Requirements-Compliance]] | ADK zip vs LangGraph · HITL · goldens |
| [[Future-Work]] | Next levers (hypotheses labeled) |
| [[Demo-Script]] | 3–5 min talk |

## Primary sources

| Doc | Role |
|---|---|
| [CONCEPTS.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/CONCEPTS.md) | Concept → code |
| [factory/runbook.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/factory/runbook.md) | Cadence + human decisions |
| [wiki Ops-Console](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Ops-Console) | Main demo UI screens + deny list |
| [docs/safety-plan.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/docs/safety-plan.md) | Safety → tests |
| [GOALS.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/GOALS.md) | OKRs |
