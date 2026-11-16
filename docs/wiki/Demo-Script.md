# Demo script (3–5 minutes)

Audience: classmates / instructors. Goal: dual-system story, gate HOLD as the insight, local console without Claude login, Cowork for real climb.

## Prep (before the room)

```bash
pip install -r requirements-console.txt -r requirements-agent.txt
streamlit run factory_console/app.py --server.port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Prefer offline or Ollama chat so the demo does not depend on Anthropic keys. Optional: have `pytest -q` green in a second terminal.

## Talk track

### 0:00–0:45 — Open Streamlit, status

- Land on **Factory loop**.
- Say: “Two systems — product is Gemma fixing GitHub issues in 28 calls; factory is Claude proposing one change at a time.”
- Point at metrics: best public **0.18**, base **V8**, candidates gated, days to deadline.
- One sentence on noise: “Same config moves a few tasks; most ‘improvements’ are noise.”

### 0:45–2:00 — One turn / HOLD example

- Open **One turn of the loop** (or Operator chat: `why V17` / `explain V14`).
- Walk base → one change → gate numbers → **HOLD**.
- Punchline: “The factory’s most useful act was refusing to ship.”

Optional: **Decision rule** page — move sliders into/out of the noise band so SUBMIT/HOLD flips live.

### 2:00–3:00 — Climb / Kaggle (climb / Kaggle)

- On stock `main`: show **Records** / leaderboard CSV as factory bookkeeping.
- Ask chat for climb / PENDING; show read-only SoT and that submit is still blocked ([#4](https://github.com/khaosans/noisegate-gemma4-factory/pull/4) merged).
- Say explicitly: console never CreateSubmission; humans / Cowork own that.

### 3:00–4:00 — Gate hold ↔ requirements

- Point at [`CONCEPTS.md`](../../CONCEPTS.md) or wiki [`Requirements-Compliance.md`](Requirements-Compliance.md): trajectory eval, statistical gate, HITL.
- Mention LangGraph supervisor as **course** evidence, not the Kaggle zip.

### 4:00–5:00 — Cowork primary loop

- Slide or wiki [`Claude-Cowork-Loop.md`](Claude-Cowork-Loop.md): Sat / Sun / Mon Skills.
- “Login-heavy Kaggle stays on Claude; this console is how you demo without that login.”
- Link artifact if useful: [Cowork project artifact](https://claude.ai/artifact/1Ldx2khByugozsHH5cuLfa).

## Lines to avoid

- Claiming Streamlit runs the Eval Gate or submits.
- Calling scripted agent sessions “Gemma competition evidence.”
- Pasting syllabus text; point at CONCEPTS / safety-plan instead.

## Backup if Streamlit is down

1. `pytest -q` + show `harness/decision_rule.py` decide() briefly.  
2. Walk the ASCII diagram in the README.  
3. Open `results/gate_runs.csv` and name one HOLD row.
