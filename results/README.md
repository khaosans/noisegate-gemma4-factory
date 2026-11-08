# Results

- `gate_runs.csv`: every Eval Gate run (30 tasks, seed 20261028, 1 repeat). Counts are per 30 tasks.
  `in_budget` = solved within 28 tool calls and 480 s, the gate metric.
- `leaderboard.csv`: every public-leaderboard submission. ~58 public tasks; we measured noise of about ±0.05.
- `eval-results.md`: the dated narrative log the factory appends to after every run and score.

**Read every comparison against the noise.** The same config moved by 3 in-budget solves between runs
(V15: 7 → 10; V8: 8 → 6), and an identical public 0.22 config scored 0.17 for us.

## Calibration log (does local eval predict the leaderboard?)

| Scored point | Local direction vs V8 | Leaderboard vs V8 | Agree? |
|---|---|---|---|
| V11 | better (10 vs 8 in-budget) | worse (0.15 vs 0.18) | No |
| V12 | slightly worse (paired 1 win / 2 losses) | worse (0.15 vs 0.18) | Yes |
| V15 | better (7, 10 vs V8 mean 7.0) | tie within noise (0.17 vs 0.18) | Inconclusive |
