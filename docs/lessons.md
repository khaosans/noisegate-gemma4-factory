# Lessons

1. **Noise dominates.** The same config moved ±3 in-budget solves between local runs, and a public
   0.22 config scored 0.17 for us. Any single comparison is mostly noise; decisions need repeated
   runs, paired comparisons, and a margin.
2. **Measure the metric that is actually scored.** Counting raw solves rewarded candidates that
   overspent the 28-call budget. Counting in-budget solves flipped V14 from "+2" to "0".
3. **The top failure is reading too long.** EMPTY_DIFF runs typically made their first edit at call
   28–30 or never. Context spent on exploration is the main cost.
4. **Prompt-only deadlines don't bind.** Gemma can't see its call count, so "by call 20" in the prompt
   didn't change behavior. Constraints the agent must obey belong in the tool layer.
5. **Local eval is only partly calibrated.** It agreed with the leaderboard on V12, disagreed on V11,
   and was inconclusive on V15.
6. **The gate's main value so far is saying no.** It held V14, V16, and V17; a factory is only as good
   as its quality control.
7. **Write the rule down before seeing the data.** The decision rule lives in code with tests, so the
   loop can't talk itself into a submission.
