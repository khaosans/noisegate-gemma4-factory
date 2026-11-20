# Eval gate results (append newest at the bottom)

## 2026-10-29 — calibration V8 / V11 / V12 (Gemma 4 Eval Gate v1, run 363369436)
30 tasks, seed 20261028, 1 repeat, 7.5 GPU-h (~5 min per candidate-task).

| Candidate | LB | Solved | Solved ≤28 calls | Empty | Edit fail | Logic | Timeout | Runs >28 calls |
|---|---|---|---|---|---|---|---|---|
| V8 | 0.18 | 9 | 8 | 7 | 2 | 11 | 1 | 16 |
| V11 | 0.15 | 13 | 10 | 5 | 2 | 8 | 2 | 15 |
| V12 | 0.15 (scored 2026-10-30) | 11 | 8 | 2 | 4 | 11 | 2 | 16 |

- Calibration FAILED (local V11 > V8; leaderboard V8 > V11). Differences are ~5/30 tasks locally and ~2/58 on the leaderboard: noise level on both sides.
- v1 verdicts (not trusted): V11 SUBMIT (already scored, never resubmit), V12 HOLD.
- About half the runs exceed 28 tool calls locally (max 49); the local harness does not enforce the cap.
- Common to all: 8 tasks always solved (fastapi_13537, fastapi_14458, requests_7309, requests_7328, rich_3043, rich_3882, rich_3894, rich_3905). Dominant failure: LOGIC_MISMATCH, then EMPTY_DIFF (V8 7 → V12 2).
- Gate v2 saved as Eval Gate version 2 (Quick Save): counts in-budget solves only; SUBMIT needs paired wins − losses ≥ 3.
- Blind prediction for V12 on the leaderboard: about equal to V8 (8 vs 8 in-budget solves). When V12's score lands, record whether this held; auto-submit stays off until a calibration point agrees.

## 2026-10-29 — gate run v4: V8 vs V14 (Eval Gate v4, run 363560117)
Started 16:46 UTC, finished ~22:00 UTC (5.2 wall h, ~10.5 GPU quota h). Same 30 tasks. Built from v2 harness cells, so the v3 fields (reads/badedits/post/tok/gold) are missing.

| Candidate | LB | Solved | In-budget | Empty | Edit fail | Logic | Timeout | Runs >28 calls | Scratch-file runs |
|---|---|---|---|---|---|---|---|---|---|
| V8 | 0.18 | 8 | 6 | 9 | 3 | 9 | 1 | 18 | 2 |
| V14 | — | 10 | 6 | 6 | 3 | 10 | 1 | 16 | 0 |

- Verdict V14: **HOLD**. Paired in-budget net 0 (win fastapi_14458, loss rich_3882); all hard checks pass (no test edits, empty/non-source and overruns not worse, zip hash OK).
- V14 raw solves +2 (fastapi_11194, requests_7328, rich_3063 gained; rich_3882 lost) but the gains came at 29–30 calls or near the 8-min limit, so they don't count in budget. The "run the issue example exactly" bullet helps correctness but costs calls.
- V8 baseline drifted between runs: 9/8 (v1) → 8/6 (v4) solved/in-budget — another sign the 30-task single-repeat gate is noise-dominated (±2–3 tasks).
- Top failure modes now: LOGIC_MISMATCH (9–10), EMPTY_DIFF (6–9), and >28-call overruns in over half of runs. Median first edit ≈ call 17. Next candidate should target budget (earlier edit / fewer calls) rather than more verification.
- GPU quota after v4: 25.3 / 30 h used this week → no further gate run until the weekly reset.

## 2026-10-30 — calibration point V12 (leaderboard 0.15)
- V12 scored **0.15** on the public leaderboard (seen 2026-10-30 08:30 UTC; submitted 10-29 03:33 UTC). Best stays V8 0.18. V11 and V12 both 0.15.
- Blind prediction "about equal to V8" did NOT hold literally (−0.03 ≈ 2 of ~58 tasks, still noise-sized).
- Direction check: local v1 paired in-budget V12 vs V8 = 1 win / 2 losses → local says V8 ≥ V12, leaderboard says V8 > V12. Direction agrees; magnitude is 1 task locally.
- Calibration status: **Pending / weak** — 1 of 2 scored points agrees in direction (V12), 1 disagrees (V11). Also LB V11 = V12 while local had V11 > V12 by 2–3 in-budget.
- Decision: auto-submit kept **OFF**; flagged to the user.
- GPU quota 25:26 / 30 h → no gate run or new candidate queued until the weekly reset.

## 2026-10-30 — strategy change: leaderboard as evaluator; V15 submitted
- Leaderboard check: #1 0.29, six teams at 0.24, hundreds at 0.22; we are 0.18 (~842/4200). The 0.22 plateau is a public notebook (flexonafft "Budget-Aware Coding Agent v2", same SuperAgent lineage as V8).
- V8 → public 0.22 diff: thinking 1024→4096, max_output_tokens 4096→8192, edit deadline call 7→12 (calls 1–8 locate/read), batched fixed-string git grep + sed range reads, heredoc fallback after 2 failed edit_file matches; drops V8's forced zero-diff edit rule. Our V11/V12 cut thinking further and scored 0.15 — consistent with thinking/edit-deadline cuts hurting.
- User decision: auto-submit ON with the leaderboard as the gate (one per UTC day, single changes off the best scored config). The Eval Gate is advisory only; calibration marked Failed.
- Submitted V15 (SuperAgent v15, run 363956732) = exact copy of the 0.22 public config, 2026-10-30 13:10 UTC. Expected ≈0.22. It becomes the base for the candidate queue in the runbook.

## 2026-10-31 — V16 built; gate run v5 queued (V15 vs V16)
- V15 still pending on the leaderboard at 00:30 UTC (no score yet). GPU quota reset: 0 / 30 h used.
- Built V16 (SuperAgent v16, run 364060382, zip sha256 d0daea5dbb847903…) = V15 + queue item 1: dropped the 3 graph tools from agent.yaml and the prompt line forbidding them; config-check assertion updated. Source verified via scriptcontent; config checks passed.
- Queued Eval Gate version 5 (run 364060907, started 00:36:52 UTC, GPU L4 x4, 4 inputs verified), built from harness v3 source with CANDIDATES = [V15 (baseline), V16], RUN_LABEL "v5 2026-10-31", same 30 tasks/seed. Expected ~5 wall h / ~10 quota h. Advisory screen only (look for crashes, empty diffs, test edits, schema/tool-call errors from the smaller tool list). First run with the V15 config locally, so it also gives a new local baseline.

## 2026-10-31 — gate run v5 result: V15 vs V16 (Eval Gate v5, run 364060907)
Started 00:36:52 UTC, last task 07:28 UTC (6h25m runtime, ~12 GPU quota h; quota 12:00 / 30 h after it). Same 30 tasks. Full v3 fields.

| Candidate | LB | Solved | In-budget | Empty | Edit fail | Logic | Timeout | Runs >28 calls | Median first edit |
|---|---|---|---|---|---|---|---|---|---|
| V15 | pending | 11 | 7 | 8 | 1 | 6 | 4 | 14 | 14.5 |
| V16 | — | 8 | 6 | 9 | 2 | 3 | 6 | 14 | 15.5 |

- Verdict V16: **HOLD** (advisory). Paired in-budget net −1 (win requests_7309; losses rich_3043 — solved but at 498 s, rich_3521 — empty diff). Hard checks: no test edits, no harness errors, hashes OK; empty/non-source 9 vs 8 and timeouts 6 vs 4 slightly worse. All gaps are noise-sized (±2–3 tasks); no breakage from dropping the graph tools. V16 stays the next leaderboard candidate once V15 scores (leaderboard is the evaluator).
- New local V15 baseline 11/7 solved/in-budget vs V8's 9/8 and 8/6 in v1/v4 — consistent with V15 ≥ V8.
- Dominant failure mode: **EMPTY_DIFF** (8 + 9 runs). Typical shape: first edit at call 28–30 or never (14 of 17), i.e. the agent reads until the budget runs out. Also two runaway edit loops (V15 rich_3782 80 calls/59 failed edits; V16 fastapi_5624 80 calls/70 failed edits).
- Next: V17 = V15 + zero-diff fallback rule (queue item 2), targeting EMPTY_DIFF.

## 2026-10-31 — V17 built; gate run v6 queued (V15 vs V17)
- Built V17 (SuperAgent v17, run 364167007, zip sha256 0fda53df30640f33…) = V15 + ONE prompt bullet after "Call 20 onward": "Zero-diff fallback: if no source edit has succeeded by call 20 (git diff would be empty), stop everything else and make your best-guess source edit now so that patch_size > 0. If edit_file keeps failing, use the heredoc Python fallback from step 3." Source diff vs V15 verified (only that line); config checks passed.
- Queued Eval Gate version 6 (run 364167955, started 08:38:17 UTC, NVIDIA L4 x4, 4 inputs verified), built from v5 harness source with CANDIDATES = [V15 (baseline), V17], RUN_LABEL "v6 2026-10-31". Harness cells identical to v5. Expected ~6.5 wall h / ~12 quota h → leaves ~5 h this week.

## 2026-10-31 — gate run v6 result: V15 vs V17 (Eval Gate v6, run 364167955)
Started 08:38:17 UTC, last task 14:14 UTC (~5.6 wall h, ~11 GPU quota h; quota 23:02 / 30 h after it). Same 30 tasks. Full v3 fields.

| Candidate | LB | Solved | In-budget | Empty | Edit fail | Logic | Timeout | Runs >28 calls | Median first edit |
|---|---|---|---|---|---|---|---|---|---|
| V15 | pending | 14 | 10 | 5 | 2 | 8 | 1 | 13 | 15 |
| V17 | — | 11 | 7 | 9 | 0 | 9 | 1 | 14 | 16 |

- Verdict V17: **HOLD** (advisory). Paired in-budget net −3 (no wins; losses fastapi_13537 — solved at 499 s, requests_7328 — solved at 30 calls/529 s, rich_3782 — logic mismatch). Hard checks: no test edits, no harness errors, hashes OK; empty/non-source 9 vs 5 and overruns 14 vs 13 worse.
- The zero-diff rule did NOT reduce EMPTY_DIFF: 8 of V17's 9 empty runs still had first edit at call 29–30 or never — Gemma ignores a mid-prompt "by call 20" deadline (no call counter visible to it). One runaway: rich_3471 52 calls / 22 post-submit calls.
- V15 local baseline drifted again: 11/7 (v5) → 14/10 (v6). Same config, ±3 tasks: confirms gate noise.
- Leaderboard order stays: V16 next after V15 scores; V17 deprioritized (weaker screen). Idea for later: enforce the deadline in the harness/tool layer (e.g. inject "call N of 28" into tool results) instead of a prompt bullet.
- No new gate run: ~7 GPU h left this week (< 11 h).

## 2026-10-31 — V15 scored 0.17 (below V8 0.18)
- V15 (exact copy of the public 0.22 notebook; submitted 10-30 13:10 UTC) scored **0.17** on the public leaderboard (seen 10-31 20:32 UTC). Best stays V8 0.18.
- Expected ≈0.22. An identical config landing 0.05 below its public score means leaderboard noise is about ±0.05 (≈3 of ~58 tasks), so V8 0.18 vs V15 0.17 is a tie and a single submission can't resolve a single-change ablation.
- Local gate had V15 ≥ V8 (11/7 and 14/10 vs 9/8 and 8/6). The leaderboard doesn't confirm it, but both differences are noise-sized.
- Per the runbook, V16/V17 are one change off V15, not off the best (V8), so auto-submit is paused pending the user's base decision. No submission on 10-31.
- GPU quota 24:11 / 30 h → no gate run until the weekly reset.

## 2026-11-09 — W46: V18 vs V19 (Run A, gate v7) → V8 vs V18 (Run B, gate v8)
- Run A (run 367009113): V18 heredoc recovery 9 solved / 7 in-budget / 7 empty / 19 overruns; V19 edit-loop cap 8/6/5/19; leader V18.
- Run B (run 367132867): V8 10/8/5/17, V18 8/7/5/20, paired net −1. V8 runs now 8/6/8 → mean 7.33.
- Decision: Δ −0.33, overrun hard check failed → **HOLD**. No W46 submission.

## 2026-11-16 — W47: V20 vs V21 (Run A, gate v9); V22 vs V23 (Run B screen, gate v11)
- Run A (run 369348902): V20 batched recon 11/7/5/17; V21 thinking 2048 6/4/15 (in-budget/empty/overruns). Both below V8 mean → Run B screened queue #5/#6.
- Gate v10 (run 370082388) was a mis-started duplicate of Run A; cancelled, results ignored.
- V20 submitted 2026-11-16 18:58 UTC at the user's request (W47 slot, gate HOLD).
- Run B screen (run 370392494): V22 best-guess source edit on empty diff 12 solved / 9 in-budget / 4 empty / 17 overruns; V23 graph tools removed 8/7/6/16; net −2. V22 Δ +1.67 < single-run bar +4 → **HOLD**; needs a second paired run vs V8.

## 2026-11-20 — V20 scored 0.13; manual team submission 0.17; loop v2 adopted
- V20 **0.13** (below V8 0.18): the in-budget metric's prediction held (calibration: agree). A manual team submission in W47 scored 0.17. Best is still V8 0.18.
- Loop v2 from 2026-11-20: decisions on KEPT14 (the 14 ever-solved tasks), V8 paired in every run, z-gate (T2 z ≥ 1.0 over ≥ 2 runs; SINGLE z ≥ 2.5; CONFIRM z ≥ 0.75), new hard check over-budget solves ≤ V8 mean + 2. V22 = CONFIRM (z 1.08).
- Next job J1 = [V8, V22] KEPT14 × 2 at the Sat 2026-11-21 heartbeat; a T2 pass queues submission S1 (not before Mon 11-23, human approval required).
- Queued next one-change hypothesis: **V24 = V8 + tool-layer read-budget cap** (enforce the read/call budget in the tool layer, not the prompt; prompt-only deadlines failed in V17). Not built, not screened.
