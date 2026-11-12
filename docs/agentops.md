# AgentOps: logs, traces, metrics

Three layers, each with one job:

| Layer | Job | Needs |
|---|---|---|
| JSONL run log (`runs/`) | Source of truth. Every step: model call, tool call + guard verdict, tool result, verify, escalation, human decision. One summary line per run. | nothing |
| `python -m agentops` | Query it: list runs, replay one run step by step, compute the checkpoint metrics, label escalations, ad-hoc SQL. | `duckdb` for `query` only |
| LangSmith | Visual trace tree per run, timing per node, datasets and online evaluators. | account + API key |

The log works offline and with no account, so the Kaggle-style setup (internet off) still
produces everything the metrics need. LangSmith is the view on top, not a dependency.

## Run Gemma through the supervisor

```bash
pip install -r requirements.txt -r requirements-agent.txt
# Gemma on the Mac via Ollama (or vLLM on a GPU box: --base-url http://localhost:8000/v1)
export NOISEGATE_BASE_URL=http://localhost:11434/v1 NOISEGATE_MODEL=<your gemma tag>
python -m supervisor --task evals/fixtures/tinycalc/task.json            # one task
python -m supervisor --task evals/fixtures/tinycalc/task.json --hitl     # pause on escalation
```

## Query

```bash
python -m agentops runs --status ESCALATED
python -m agentops show 20261111T222027-f85667
python -m agentops metrics --config supervisor-v1
python -m agentops label 20261111T222027-f85667 warranted
python -m agentops query "SELECT reason, count(*) FROM events WHERE kind='tool_call' AND verdict<>'allow' GROUP BY 1"
python -m evals.safety.run            # G6-G17 block rate and false-positive rate
```

## LangSmith (optional)

```bash
export LANGSMITH_TRACING=true LANGSMITH_PROJECT=noisegate LANGSMITH_API_KEY=...   # never commit
```

Each run is traced as `noisegate <task_id>` with tags `noisegate`, `<config>` and metadata
`run_id`, `task_id`, `config`, so a LangSmith trace and a JSONL run share the same `run_id`.
The fixture and benchmark tasks are public or synthetic; check LangSmith's data terms before
tracing private repositories, or self-host Langfuse instead (it accepts the same LangChain
callbacks).

## What to watch weekly

The safety eval must stay at 100% blocked and 0% false positives; any change to
`guardrails/` reruns it in `pytest`. For live Gemma runs, track in-budget resolution,
`empty_diff_rate` and `budget_overrun_rate` against V8's gate numbers, and review every
escalation once so `escalation.precision` means something.
