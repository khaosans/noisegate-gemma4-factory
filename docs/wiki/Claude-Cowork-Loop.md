# Claude Cowork loop (primary agentic path)

The factory’s **production** climb path is Claude, not Streamlit. Cowork / Project wakes hold the authenticated Kaggle browser session needed for notebook commit, Eval Gate starts, and CreateSubmission.

Cowork project artifact: [claude.ai/artifact/1Ldx2khByugozsHH5cuLfa](https://claude.ai/artifact/1Ldx2khByugozsHH5cuLfa).  
Paper Ops Console (replay): [claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW).  
In-repo procedures: [`factory/`](https://github.com/khaosans/noisegate-gemma4-factory/tree/main/factory) (`project-instructions.md`, `runbook.md`, `skills/*/SKILL.md`).

## Why Claude holds login-heavy ops

| Action | Why not Streamlit |
|---|---|
| Import / Save & Run All on SuperAgent notebook | Needs logged-in Kaggle UI |
| Start Eval Gate on 4× L4 | GPU quota + notebook auth |
| CreateSubmission | Human-reserved; daily/weekly limits |
| Dashboard refresh after scoring | Session + judgment on unexpected UI |

The console is a **query and demo surface** over repo records. It deliberately cannot start gates or submit.

## Schedule (UTC)

From [`factory/runbook.md`](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/factory/runbook.md). GPU quota resets weekly (by Sat 00:30 UTC).

| Day | Work |
|---|---|
| **Sat** | Build top queue items as C1/C2 (base + one change); Gate **Run A** screen |
| **Sun** | Gate **Run B**: leader vs V8 (or next pair if both below V8 mean) |
| **Mon** | Apply `decision_rule.py`; submit only on SUBMIT; ≤1 gated submit / ISO week |
| Other wakes | Status only: record scores, refresh dashboards |

Planned submission slots (from runbook): Nov 9, 16, 23, 30. No gate runs after Nov 30. Final deadline **2026-12-02**.

## Skills (procedural memory)

| Skill | Role |
|---|---|
| `build-candidate` | Export base, apply exactly one change, verify diff + SHA-256 |
| `run-eval-gate` | Drive Gate Run A (screen two) / Run B (leader vs V8, or next pair if both trail V8) |
| `weekly-decision` | Apply coded SUBMIT/HOLD rule; report to humans |
| `record-score` | After LB returns, update `results/` and note gate↔LB agreement |

Project knowledge on every wake: runbook + `results/eval-results.md`. System prompt: `factory/project-instructions.md`.

## Human decisions the loop never makes

- Base config (e.g. 2026-11-07 rollback to V8; V15 lineage retired as base)
- Cadence (one gated submission / week; two candidates screened / week)
- Final two selections for private scoring
- CreateSubmission itself

## Cost guardrails

- One gate run at a time; start only with ≥12 GPU-quota hours left; two runs per quota week
- On run error: fix only a clear harness bug and re-run once; second error stops the loop
- No ad-hoc runs, larger task sets, or interactive GPU sessions
- Same UI step fails 3× → stop and report

## Relation to the local console

Classmates can follow the story on `:8765` without Claude login. The authentic climb still goes through this Cowork loop. Merged [#3](https://github.com/khaosans/noisegate-gemma4-factory/pull/3) / [#4](https://github.com/khaosans/noisegate-gemma4-factory/pull/4) only improve the local query surface (Ollama chat, read-only climb SoT).
