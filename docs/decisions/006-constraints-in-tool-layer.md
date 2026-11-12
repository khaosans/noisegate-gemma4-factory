# 006. Enforce budget constraints in the tool layer, not the prompt

**Status:** Proposed (queue item 7)

## Context
V17 added "make a best-guess edit if the diff is empty by call 20." EMPTY_DIFF did not drop: 8 of
V17's 9 empty runs still made their first edit at call 29–30 or never. Gemma has no visible call
counter, so a deadline stated in the prompt is not something it can track.

## Decision (proposed)
If the submission format allows, surface the budget to the agent inside tool results
(e.g. "call 19 of 28") rather than as a prompt rule.

## Update (2026-11-11)
Implemented in the local LangGraph supervisor (decision 007): every tool result starts with
`[call N of 28 | S s left]`, and the budget is enforced in code. Whether the Kaggle runtime
allows the same remains open.

## Open question
Whether the competition's agent config lets a submission change tool-result text. Investigate
without GPU before adding it to the queue.
