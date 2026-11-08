# 004. Roll back the base to V8

**Status:** Accepted (2026-11-07, human decision)

## Context
V15 (0.17) became the base under 003, and V16/V17 were built on it. V8 (0.18) remained the best
scored config. Locally V15 looked ≥ V8, but every difference was noise-sized.

## Decision
V8 is the base. V15 lineage is retired as a base; V16/V17 are never submitted. V15 is kept as a
different-lineage hedge for final selection.

## Consequences
- The candidate queue was rebuilt on V8, porting V15's ideas one at a time (heredoc recovery,
  batched recon, larger thinking budget).
- The V8 baseline gets a new local run every week (Run B), so its mean keeps improving.
