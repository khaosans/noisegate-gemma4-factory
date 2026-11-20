# Demo script (3–5 minutes)

Audience: classmates / instructors. Goal: dual-system story, gate HOLD as the insight, **Claude Ops Console as the default UI**, Cowork for real climb. Streamlit is optional.

## Prep (before the room)

**Default — no local server required:**

1. Open [[Ops-Console]] → [Claude Agent Ops Console artifact](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW).  
2. Optional: have `pytest -q` green in a terminal if you want a code aside.

**Optional only — Streamlit** (when you need live checkout files):

```bash
pip install -r requirements-console.txt -r requirements-agent.txt
streamlit run factory_console/app.py --server.port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Prefer offline or Ollama chat so the demo does not depend on Anthropic keys. Expect rough edges — [[Local-And-Streamlit]].

## Talk track

### 0:00–0:45 — Open Claude Ops Console (default)

- Land on the [Ops Console artifact](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW).
- Say: “Two systems — product is Gemma fixing GitHub issues in 28 calls; factory is Claude proposing one change at a time. This console is our default demo UI.”
- Point at factory / HOLD / HITL narrative (agent lifecycle, noise gate).
- One sentence on noise: “Same config moves a few tasks; most ‘improvements’ are noise.”

### 0:45–2:00 — HOLD as the insight

- Walk one delta → paired gate → **HOLD** inside the V8 noise band.
- Punchline: “The factory’s most useful act was refusing to ship.”
- Say explicitly: consoles never CreateSubmission; humans / Cowork own that.

Optional (Streamlit only): **Decision rule** page — move sliders into/out of the noise band so SUBMIT/HOLD flips live.

### 2:00–3:00 — Climb / Kaggle

- Scores that count live in `results/` / climb SoT — not invented from the paper UI.
- Ask: climb / PENDING stays on Cowork; submit is still blocked from any console.
- Optional Streamlit: **Records** / leaderboard CSV as factory bookkeeping ([#4](https://github.com/khaosans/noisegate-gemma4-factory/pull/4) merged).

### 3:00–4:00 — Gate hold ↔ requirements

- Point at [[Method-Card]] or [CONCEPTS.md](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/CONCEPTS.md) / [[Requirements-Compliance]]: trajectory eval, statistical gate, HITL.
- One line on goldens: **55/55** adversarial blocked, **0/29** false positives (`evals/safety`).
- Mention LangGraph supervisor as **course** evidence, not the Kaggle zip.

### 4:00–5:00 — Cowork primary climb loop

- Slide or [[Claude-Cowork-Loop]]: Sat / Sun / Mon Skills.
- “Login-heavy Kaggle stays on Claude Cowork; the Ops Console is how you demo the factory story by default.”
- [[Ops-Console]] (default): https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW · Cowork climb artifact: https://claude.ai/artifact/1Ldx2khByugozsHH5cuLfa

## Lines to avoid

- Treating Streamlit as the default demo path.
- Claiming either console runs the Eval Gate or submits.
- Calling scripted agent sessions “Gemma competition evidence.”
- Pasting syllabus text; point at CONCEPTS / safety-plan instead.

## Backup if the artifact link is down

1. Optional Streamlit `:8765` (rough) — same deny list.  
2. `pytest -q` + show `harness/decision_rule.py` decide() briefly.  
3. Walk the Figure 1 Mermaid on [[Home]] / the [README](https://github.com/khaosans/noisegate-gemma4-factory#readme).  
4. Open `results/gate_runs.csv` and name one HOLD row.
