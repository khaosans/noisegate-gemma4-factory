# 001. Every candidate is the base plus exactly one change

**Status:** Accepted (2026-10-29)

## Context
One leaderboard submission per day, ~1.5 days to score, and noise of about ±0.05 per submission.
Bundling several changes makes any result impossible to attribute.

## Decision
A candidate = current base + one change (one prompt bullet, one config value, or one tool-list edit).
Full-config imports (V15) are allowed only as labeled exceptions and credited.

## Consequences
- Results map to a single cause, so the queue can be reasoned about.
- Progress per week is slow; the queue must be ordered by expected impact.
- V16/V17 were one change off V15, so they lost their meaning when the base changed (see 004).
