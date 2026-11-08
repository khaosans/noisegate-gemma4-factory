# 003. Use the leaderboard as the evaluator (daily auto-submit)

**Status:** Superseded by 004 and 005 (in effect 2026-10-30 to 2026-11-07)

## Context
Local calibration had failed: the gate ranked V11 above V8, the leaderboard ranked V8 above V11.
Meanwhile a public notebook scored 0.22 vs our 0.18.

## Decision
Make the leaderboard the gate: submit one single-change candidate per day off the best scored
config; the Eval Gate becomes advisory. Start by submitting an exact, credited copy of the public
0.22 config (V15).

## What happened
V15 scored **0.17**. An identical config landing 0.05 below its public score showed that a single
submission cannot resolve a single-change ablation. The leaderboard is a noisier gate than our own.

## Why it was reversed
Daily submissions spend the scarcest resource (submissions) on noise. See 004 and 005.
