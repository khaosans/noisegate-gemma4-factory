---
name: run-eval-gate
description: Start, monitor, and parse an Eval Gate run on Kaggle (2 configs x 30 tasks on 4x L4). Use for the weekly Run A (screen two candidates) and Run B (leader vs V8), and to parse a completed run's Score lines.
---
# Preconditions (all required)
- No Eval Gate session is queued or running.
- GPU quota left ≥ 12 h; fewer than 2 gate runs this quota week.

# Start a run
1. Take the harness source from Eval Gate version 3, 5, 6 or a later version built from them (7–9, 11).
   Never 4 (old v2 cells) or 10 (mis-started duplicate). Verify the settings by parsing the imported source.
2. In the settings cell, set `CANDIDATES` (two configs: label, version, run id, LB score, code),
   `BASELINE`, and `RUN_LABEL` ("vN YYYY-MM-DD A" or "B"). Seed and task set stay fixed.
3. Import, reload the editor, confirm the 4 inputs and GPU L4 x4, then Save & Run All.

# Parse a finished run
1. Collect all cell output text; keep lines containing "Score " and "solved=".
2. `harness.trajectory.parse_log(lines)` → dedupe and type them.
3. `RunSummary.from_results(...)` per candidate; `paired_net(...)` for Run B.
4. Schemas: `factory/state-and-artifacts.md`. Append a row per candidate to `results/gate_runs.csv` and a dated section to `results/eval-results.md`.

# On error
Fix only a clear harness bug and re-run once (quota permitting). Second error → stop and report.
