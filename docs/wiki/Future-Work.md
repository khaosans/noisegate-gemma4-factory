# Future work

Concrete next steps. Same bullets as the README, with rationale. None of these expand the competition MVP beyond the frozen product ship path.

## 1. Console Ollama + climb/Kaggle read-only bridge — done

**PRs:** [#3](https://github.com/khaosans/noisegate-gemma4-factory/pull/3) (Ollama backend), [#4](https://github.com/khaosans/noisegate-gemma4-factory/pull/4) (climb bridge) — **merged**.

**Status:** Local query can answer “where are we?” / “any PENDING?” without Claude login. CreateSubmission and gate-start stay human. Climb `docs/scoreboard.json` remains the live publicScore SoT; NoiseGate CSV is bookkeeping.

## 2. Propose `record_score` from COMPLETE Kaggle rows

**Why:** After a tip scores, waking Claude (or the console) should draft the CSV/log entry from COMPLETE rows instead of retyping. **Approve** remains required before any write — same HITL as today.

**Done when:** A queued `record_score` payload can be filled from climb/Kaggle COMPLETE data; UI Approve still gates the write; no auto CSV overwrite.

## 3. Frugal local Gemma supervisor demos

**Why:** Course checkpoints ask for supervised tool loops with guardrails. Scripted sessions already show the graph; a tool-capable local Gemma tag via Ollama makes the demo feel real without burning Kaggle GPU.

**Constraints:** Sandbox-required; separate from the ADK zip; never described as competition evidence about the hosted Gemma runtime.

## 4. Calibration: more decisive gate↔leaderboard points

**Why:** OKR O2 wants ≥2 of 3 scored points agreeing in direction with the leaderboard. Today we have partial agreement and large noise (±3 local, ±0.05 LB). Need more decisive SUBMIT decisions and a noise re-measure after any harness change.

**Done when:** Updated calibration notes in `results/`; explicit agree/disagree/inconclusive tally vs GOALS.

## 5. Optional course fallback evidence pack

**Why:** If graders need a non-competition narrative, package: LangSmith (or AgentOps) traces + one guardrail story + 3–5 golden cases from `evals/` / recorded sessions — without inventing a second product.

**Done when:** A short index under `docs/` or the presentation map points at those artifacts; PROBLEM.md only updated if the graded track formally falls back (out of scope for this docs pack alone).

## Non-goals (still)

- CreateSubmission from Streamlit
- Secrets or credentials in-repo
- Re-implementing Agent OS here
- Treating the React Ops Console live cycle as invented scores (replay of recorded runs only)
