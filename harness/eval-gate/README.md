# Eval Gate (local evaluation harness)

Kaggle notebook: [Gemma 4 Eval Gate](https://www.kaggle.com/code/souriyakhaosanga/gemma-4-eval-gate).
Runs each candidate's agent on a fixed set of 30 tasks (seed 20261028, 1 repeat) and prints one
`Score` line per task (format in `harness/trajectory.py`).

| | |
|---|---|
| Hardware | 4× NVIDIA L4, internet off |
| Environment | pinned 2026-06-30 image, Python 3.12 (the wheelhouse needs 3.12; a fresh notebook gets 3.13 and fails) |
| Inputs | competition data, plugins dataset, wheelhouse dataset, Gemma 4 model V2 |
| Cost | ~5–7 min per candidate-task; one 2-config × 30-task run ≈ 5–6.5 wall h ≈ 10–12 GPU-quota h |
| Valid harness sources | notebook versions 3, 5, 6 (never 4: built from v2 cells) |

## Notebook files

Place the exported cells here: `template.ipynb` plus one `*_cell.py` per code cell
(from `labs/gemma-eval-harness/` in the original repo). Clear outputs and delete
`metadata.kaggle` before committing; importing a notebook whose metadata lists data sources
wipes the editor's inputs and accelerator.

## What the harness does not do

- It does not enforce the 28-call cap; overruns are counted, and `in_budget` excludes them.
- It is not the leaderboard: 30 local tasks vs ~58 hidden ones, measured noise ±2–3 tasks per run.
