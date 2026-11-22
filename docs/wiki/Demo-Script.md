# Demo script (3–5 minutes)

Audience: classmates / instructors. Goal: dual-system story, gate HOLD as the insight, **Claude Ops Console as the main UI**, Cowork for real climb.

## Prep (before the room)

1. Open [[Ops-Console]] → [Claude Agent Ops Console artifact](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW).  
2. Optional: have `pytest -q` green in a terminal if you want a code aside.

## Talk track

### 0:00–0:45 — Open Claude Ops Console

- Land on the [Ops Console artifact](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW).
- Say: “Two systems — product is Gemma fixing GitHub issues in 28 calls; factory is Claude proposing one change at a time. This console is our main demo UI.”
- Point at overview: factory status, best score context, control surface.
- One sentence on noise: “Same config moves a few tasks; most ‘improvements’ are noise.”

### 0:45–2:00 — HOLD as the insight

- Walk one delta → paired gate → **HOLD** inside the V8 noise band (**7.33 ± 2.5** / 30) — HOLD close-up on [[Ops-Console]]; chart + rubric on [[Trajectory-Eval-Rubric]].
- Punchline: “The factory’s most useful act was refusing to ship.”
- Say explicitly: this console never CreateSubmission; humans / Cowork own that.

### 2:00–3:00 — Agents + HITL

- Show the agents panel: watchdog / patch / eval-runner / submit-governor.
- Call out HITL guardrails on full gate runs.
- Scores that count live in `results/` / climb SoT — not invented from the paper UI.

### 3:00–4:00 — Gate hold ↔ requirements

- Point at [[Method-Card]], [[Trajectory-Eval-Rubric]], or [CONCEPTS.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/CONCEPTS.md) / [[Requirements-Compliance]]: trajectory eval, statistical gate, HITL.
- One line on goldens: **55/55** adversarial blocked, **0/29** false positives (`evals/safety`).
- **Runtimes talking point (2–3 sentences):** We separate **policy** (plain Python) from **runtime**. That lets us ship a lean single-agent ADK zip to Kaggle under 28 calls / 480s — without CrewAI-style multi-agent chatter — while proving stateful guardrails and `hitl` interrupts locally in LangGraph `supervisor/` as course evidence, not as the competition supervisor. Detail: [Policy vs. Agent Runtimes (Why This Stack)](Architecture#policy-vs-agent-runtimes-why-this-stack).

### 4:00–5:00 — Cowork primary climb loop

- Slide or [[Claude-Cowork-Loop]]: Sat / Sun / Mon Skills.
- “Login-heavy Kaggle stays on Claude Cowork; the Ops Console is how you demo the factory story.”
- [[Ops-Console]]: https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW · Cowork climb artifact: https://claude.ai/artifact/1Ldx2khByugozsHH5cuLfa

## Lines to avoid

- Claiming the Ops Console runs the Eval Gate or submits.
- Calling scripted agent sessions “Gemma competition evidence.”
- Pasting syllabus text; point at CONCEPTS / safety-plan instead.
- Inventing `publicScore` from the paper UI.

## Backup if the artifact link is down

1. `pytest -q` + show `harness/decision_rule.py` decide() briefly.  
2. Walk Figure 1 (three bands) on [[Architecture]] / the [README](https://github.com/khaosans/noisegate-gemma4-factory#readme).  
3. Open `results/gate_runs.csv` and name one HOLD row.
