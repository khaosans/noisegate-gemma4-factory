# Candidates

Every candidate is **the current base + exactly one change**, so a gate result can be attributed
to that change. Numbers are in-budget solves per 30 tasks; see `results/` for full tables.

| Version | Base | The one change | Gate | Leaderboard |
|---|---|---|---|---|
| V8 | — | base | 8, 6 (mean 7.0) | **0.18** |
| V11 | V8 | thinking budget cut | 10 (calibration run) | 0.15 |
| V12 | V11 | variant of V11 | 8 (calibration run) | 0.15 |
| V13 | — | accidental duplicate of V12 | — | never used |
| V14 | V8 | verify bullet: "run the issue example with `python -c`" | 6, net 0 → HOLD | — |
| V15 | — | exact copy of the public 0.22 notebook ([flexonafft](https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2)) | 7, 10 | 0.17 |
| V16 | V15 | removed the 3 unused graph tools | 6, net −1 → HOLD | — |
| V17 | V15 | prompt bullet: "best-guess source edit if diff empty by call 20" | 7, net −3 → HOLD | — |

V15 is a full-config import, not a one-change candidate; it is credited to its author and kept as
a different-lineage hedge. V16 and V17 are retired because the base was rolled back to V8
(see `docs/decisions/004`).

## V8 → public 0.22 config (V15), the differences

thinking 1024 → 4096; max_output_tokens 4096 → 8192; edit deadline call 7 → 12; batched fixed-string
`git grep` + `sed` range reads; python heredoc fallback after 2 failed `edit_file` matches; no forced
zero-diff edit.

## Queue (base V8, two screened per week)

1. Heredoc edit-failure recovery (from V15).
2. Stop after 3 failed edits in a row on one region, re-read once, then fall back.
3. Batched recon: one `git grep -n` + one `sed -n` range per hypothesis.
4. thinking_budget 1024 → 2048.
5. Zero-diff fallback edits likely source, not a docstring.
6. Remove the 3 dead graph tools.
7. Investigate: show the agent "call N of 28" in tool results (constraint in the tool layer).
