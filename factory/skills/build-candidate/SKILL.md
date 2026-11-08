---
name: build-candidate
description: Build one climb-loop candidate as a new Gemma 4 SuperAgent notebook version (current base + exactly one queue change) and verify it. Use on the Saturday wake, or whenever a queue item needs to become a submittable version.
---
# Inputs
- Current base version (see `product/candidates.md`) and the queue item to apply.

# Steps
1. Export the base version's notebook source; delete `metadata.kaggle`; clear outputs.
2. Apply exactly ONE change (prompt line, config value, or tool list). Keep the FILES layout and the
   `submission.zip` writer unchanged.
3. Import into the SuperAgent notebook editor and run "Save & Run All (Commit)".
4. Verify the new version: its source diff vs base is only the intended change, config checks
   pass, and the printed SHA-256 matches the downloaded zip.
5. Mark the queue item "tried" in `product/candidates.md` with the version number.

# Stop conditions
- Diff touches more than the intended change → discard the version, report.
- Same UI step fails 3 times → stop, report.
