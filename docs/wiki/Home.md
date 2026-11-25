# NoiseGate Gemma 4 Factory

> Preferred viewer: this [GitHub Wiki](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Home). Editors sync from in-repo `docs/wiki/`.

An autonomous **build → evaluate → submit** loop that separates real agent improvements from benchmark noise.

The public notebook that shows **0.22** scored **0.17** when we submitted it. Baseline **V8** fluctuates **8 / 6 / 8** on the same 30 tasks. Host limit is **1 CreateSubmission / UTC day**; quality bars decide who may use the slot — [[Submit-Policy]].

| | |
|---|---|
| Authors | Souriya Khaosanga · Adil Shamim |
| Competition | [Gemma 4 Developer Agent](https://www.kaggle.com/competitions/gemma-4-developer-agent) · deadline 2026-12-02 |
| Best public (base) | **0.18** (V8) |
| Repo | [noisegate-gemma4-factory](https://github.com/khaosans/noisegate-gemma4-factory) |
| Video | https://youtu.be/-EiKv_MafOY |
| Ops Console (main UI) | [artifact](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW) · [[Ops-Console]] |

**Score SoT:** factory base is **V8 @ 0.18**. Sibling [`cmu-agentic-ai`](https://github.com/khaosans/cmu-agentic-ai) climb tips use a separate ledger (`docs/scoreboard.json`) — do not conflate.

## Architecture at a glance

Three bands (diagram lives on [[Architecture#figure-1--three-bands]]):

| Band | Job |
|---|---|
| **Factory** | One delta → paired gate → coded HOLD/SUBMIT · 1/UTC-day |
| **Product** | Gemma 4 ReAct · ≤28 calls / ≤480s / fixed seed |
| **Ops Console** | Replay + HITL · **never** CreateSubmission |

*Insight.* Gains inside V8’s **±2.5** band are **HOLD**. Chart + scoring: [[Trajectory-Eval-Rubric]] · full stack: [[Architecture]].

## Demo in under a minute

1. Open the [[Ops-Console]] Claude artifact (main UI).
2. Show a **HOLD** inside the V8 noise band (**7.33 ± 2.5** / 30) — [[Trajectory-Eval-Rubric]].
3. Climb / CreateSubmission path = Claude Skills ([[Claude-Cowork-Loop]]), not the console.

Full talk track: [[Demo-Script]].

## Pages

| Section | Page | Use when you need… |
|---|---|---|
| Start | [[Method-Card]] | One-page problem → method → evidence |
| Start | [[Demo-Script]] | 3–5 min talk track |
| How it works | [[Architecture]] | Figures, runtimes, policy vs ADK/LangGraph |
| How it works | [[Trajectory-Eval-Rubric]] | Noise-band chart, 4-tier scoring, failure modes |
| How it works | [[Submit-Policy]] | 1/UTC-day + quality bars before HITL submit |
| Operate | [[Ops-Console]] | Main demo UI screens + deny list |
| Operate | [[Claude-Cowork-Loop]] | Sat/Sun/Mon Skills + loop v2 ledger |
| Evidence | [[Requirements-Compliance]] | ADK zip vs LangGraph · HITL · goldens |
| Evidence | [[Future-Work]] | P0–P4 map · V22 confirm · V24 hypothesis · [pre–Dec 2 sprint](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/docs/sprint-pre-dec2.md) |

Streamlit / local console is **not** the demo path — see [[Local-And-Streamlit]] only if you need that caveat.

## Primary sources (repo)

| Doc | Role |
|---|---|
| [CONCEPTS.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/CONCEPTS.md) | Concept → code |
| [factory/runbook.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/factory/runbook.md) | Cadence + human decisions |
| [docs/TRAJECTORY_RUBRIC.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/docs/TRAJECTORY_RUBRIC.md) | Rubric field-map SoT (viewer: [[Trajectory-Eval-Rubric]]) |
| [docs/safety-plan.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/docs/safety-plan.md) | Safety → tests |
| [GOALS.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/GOALS.md) | OKRs |
