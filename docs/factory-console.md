# Factory console: demo app and operator chatbot

A Streamlit app over the factory's own records. It shows how the factory builds the coding agent
(one change, measured on the benchmark, shipped only above the noise) and lets you query and run
the factory from a chat.

```bash
pip install -r requirements-console.txt -r requirements-agent.txt
streamlit run factory_console/app.py --server.port 8765
```

### Local Ollama (optional query backend)

The operator chat can call a local OpenAI-compatible Ollama endpoint instead of Claude:

```bash
ollama serve   # if not already running
ollama pull llama3.2:3b
export FACTORY_CONSOLE_BACKEND=ollama
export OLLAMA_HOST=http://127.0.0.1:11434   # optional; also accepts OLLAMA_API_BASE
export OLLAMA_MODEL=llama3.2:3b             # optional; falls back to NOISEGATE_MODEL / first chat tag
streamlit run factory_console/app.py --server.port 8765
```

If Ollama is down with `FACTORY_CONSOLE_BACKEND=ollama`, the chat shows a clear error and falls back to offline keyword mode. With `FACTORY_CONSOLE_BACKEND=auto` (default), the order is Claude → Ollama → offline.

## Pages

| Page | What it shows | Data |
|---|---|---|
| Factory loop | The loop, current state, what the runbook says is due today, stale or missing records | `results/`, `factory/runbook.md` |
| One turn of the loop | One candidate from its one change through the gate to the verdict | `results/gate_runs.csv`, `harness/decision_rule.py` |
| Noise | Same config across runs, leaderboard ±0.05, what happened to each of the 30 tasks | `results/` |
| Decision rule | Sliders into the real `decide()`; verdict updates live | `harness/decision_rule.py` |
| Judge a gate log | Paste Eval Gate output: task grid, paired net, verdict | `harness/trajectory.py` |
| Agent sessions | One supervised run call by call on a 28-slot ruler, with guardrail verdicts | `runs/` (agentops JSONL) |
| Operator chat | Ask questions and run local jobs in plain language | all of the above |
| Records | Queue, candidates, goals, decisions, lessons, the dated log | `product/`, `docs/`, `GOALS.md` |

## Operator chat

`factory_console/actions.py` is the list of things the console may do. The chat and the pages call
the same functions.

- **Query:** gate runs, leaderboard, candidates and queue, decisions, lessons, goals, the log, run logs.
- **Check:** status against the runbook, replay the decision rule on a recorded candidate, what-if
  numbers, judge a pasted gate log.
- **Run:** the test suite, the safety eval, a zip build with SHA-256s, one supervised agent session.
- **Not available, on purpose:** starting a Kaggle gate run, submitting, changing the base config.
  The runbook reserves these for humans.
- **Writes need approval:** `record_score` only queues an entry. It is written to `results/` after
  you press Approve in the chat page.

Chat backends (`FACTORY_CONSOLE_BACKEND`, default `auto`):

| Backend | When | Notes |
|---|---|---|
| Claude | `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` | Model `claude-opus-5-5` (override with `FACTORY_CONSOLE_MODEL`). Server-side refusal fallback enabled. |
| Ollama | daemon on `OLLAMA_HOST` (default `http://127.0.0.1:11434`) | OpenAI-compatible `/v1/chat/completions` + tools. Model from `OLLAMA_MODEL` / `NOISEGATE_MODEL` / first non-embed tag. |
| Offline | nothing else available | Keyword router over the same actions (`status`, `why V17`, `what if 9 8 net 1`, `run tests`, …). |

`auto` tries Claude, then Ollama, then offline. A live-backend failure mid-turn falls through the same chain and says so in the reply.

## What is real and what is a stand-in

- Gate and leaderboard numbers are the recorded ones. Verdicts on "One turn of the loop" are a
  replay under today's rule; `gate_runs.csv` has no time-overrun or non-source columns, so the
  replay uses call overruns and EMPTY_DIFF counts only.
- The default text on "Judge a gate log" is a **synthetic 8-task sample**
  (`factory_console/sample_gate_log.txt`). Paste a real notebook log to replace it.
- "Run scripted session" uses a **scripted model, not Gemma**. It shows the supervisor, sandbox and
  guardrails (it tries a test-file edit, which is blocked). "Run Gemma session" needs a local
  endpoint: start Ollama, pull a Gemma tag that supports tool calling, set `NOISEGATE_MODEL`.
- The real Eval Gate runs on Kaggle (4× L4, about 6 hours). The console does not run it.
