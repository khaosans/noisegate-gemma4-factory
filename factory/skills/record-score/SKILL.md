---
name: record-score
description: Record a newly scored leaderboard submission, update the base if warranted, and log calibration. Use on any wake where the Kaggle submissions page shows a score not yet in results/leaderboard.csv.
---
# Steps
1. Append the score to `results/leaderboard.csv` and a dated note to `results/eval-results.md`.
2. Calibration: compare the gate's direction (candidate vs V8) with the leaderboard's; add a row
   to the calibration table in `results/README.md`.
3. If score ≥ current best → the candidate becomes the new base; re-apply remaining queue items on
   top of it. Otherwise keep the base and mark the candidate "passed gate, LB lower".
4. Update the status column in `GOALS.md`.
