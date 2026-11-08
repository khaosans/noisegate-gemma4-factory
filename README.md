# A Software Factory for a Gemma 4 Coding Agent

**Souriya Khaosanga · Adil Shamim** · CMU SCS Agentic AI · Kaggle *Google DeepMind Gemma 4 Developer Agent*

We built two systems. The **product** is a Gemma 4 coding agent that fixes real GitHub issues.
The **factory** is a Claude-run loop that proposes, builds, evaluates, and ships new versions of
that agent, with humans controlling the decisions that matter. Our main finding: in a self-improving
system, the evaluation harness matters more than the generator. Most of the differences we measured
were noise, and the factory's most useful act was refusing to ship.

| | |
|---|---|
| Best public score | **0.18** (V8, current base) |
| Versions evaluated / held by our gate | 7 / 3 (V14, V16, V17) |
| Measured noise | ±2–3 tasks per 30 locally · ±0.05 on the leaderboard |

## The challenge

A Gemma 4 agent (`gemma-4-31b-it`, fixed by the rules) gets a repository (fastapi, requests, rich, …)
and an issue, and must produce a patch within **28 tool calls and ~8 minutes**. Hidden tests score
the patch. Kaggle allows one submission per day; scoring takes ~1.5 days; final deadline Dec 2, 2026.

## Two systems

```
┌─────────────────────────── FACTORY (Claude, scheduled wakes) ───────────────────────────┐
│  queue ─► build candidate ─► Eval Gate (2 runs) ─► decision rule ─► submit ─► score     │
│              (base + 1 change)    4× L4, 30 tasks     code + tests     ≤1/week   │       │
│                     ▲                                                            │       │
│                     └──────────── new base if score ≥ best ◄─────────────────────┘       │
│   HUMANS decide: base config · cadence · final two selections                           │
│                                                                                          │
│        ┌──────────── PRODUCT (Gemma 4 SuperAgent) ────────────┐                          │
│        │ agent.yaml · sampling.yaml · system prompt call plan │                          │
│        └──────────────────────────────────────────────────────┘                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

## Repository map

| Path | What it is |
|---|---|
| [`product/`](product/) | The submitted agent config, build script, and every candidate's one change |
| [`harness/`](harness/) | Trajectory parser, evaluators E1–E9, and the SUBMIT/HOLD decision rule (tested) |
| [`harness/eval-gate/`](harness/eval-gate/) | The Kaggle evaluation notebook and its environment notes |
| [`factory/`](factory/) | The loop: runbook, Project instructions, and four Claude Skills |
| [`results/`](results/) | Every gate run and leaderboard score, plus the calibration log |
| [`docs/decisions/`](docs/decisions/) | Decision records, including one we reversed |
| [`GOALS.md`](GOALS.md) | Objectives and key results, with status |
| [`CONCEPTS.md`](CONCEPTS.md) | Course concepts → where each one lives in the code |
| [`presentation/`](presentation/) | Slides, video link, and the slide → repo map |

## Results

| Version | Change | Local in-budget solves /30 | Public score |
|---|---|---|---|
| V8 | base | 8, 6 | **0.18** |
| V11 | thinking budget cut | 10 | 0.15 |
| V12 | variant of V11 | 8 | 0.15 |
| V14 | + "run the issue example" | 6 → held | — |
| V15 | public 0.22 notebook, credited | 7, 10 | 0.17 |
| V16 | V15 − unused graph tools | 6 → held | — |
| V17 | V15 + "edit by call 20" rule | 7 → held | — |

Full tables: [`results/`](results/). Lessons: [`docs/lessons.md`](docs/lessons.md).

## Quick start

```bash
pip install -r requirements.txt
pytest -q                                  # decision rule + parser tests
python product/build_submission.py         # rebuild submission.zip, print SHA-256s
```

Parse an Eval Gate log and apply the rule:

```python
from harness.trajectory import parse_log
from harness.decision_rule import RunSummary, V8_HISTORY, decide, paired_net

rows = parse_log(open("gate_output.txt"))
cand = [r for r in rows if r.candidate == "C1"]
v8 = [r for r in rows if r.candidate == "V8"]
print(decide([RunSummary.from_results(cand)], V8_HISTORY + [RunSummary.from_results(v8)],
             run_b_paired_net=paired_net(cand, v8),
             zip_sha_ok=True, one_change_off_base=True, never_scored=True))
```

## What is not in this repo

Competition data and tasks, model weights, the GPU wheelhouse, Kaggle credentials, and other
teams' code. V15 is described and credited, not copied:
[flexonafft, *Budget-Aware Coding Agent v2*](https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2).

## License

MIT. See [`LICENSE`](LICENSE).
