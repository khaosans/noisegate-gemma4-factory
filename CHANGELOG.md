# Changelog

All notable changes to NoiseGate Gemma 4 Factory are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning is Capstone **beta SemVer** (`X.Y.Z-beta.N`) until an explicit human GA cut.

## [Unreleased]

### Added
- Architecture wiki: **Policy vs. Agent Runtimes** Mermaid + trade-off table (ADK product · LangGraph local · factory wakes); Requirements-Compliance + Demo-Script + README aligned
- Wiki [[Submit-Policy]] — design SoT for loosened submit cadence (**1 / UTC day** only) and risk-tiered bars (5-task V8-derived · 7-task safety when tools/edit flagged · strict-win external · pre-flight ≤11.2 h)
- Future-Work wiki: P0–P4 priority Mermaid (V22 confirm → V24 → calibration → record_score → local demos); shipped items moved out of “next”

### Changed
- Runbook / Cowork / Architecture / Method-Card / Requirements / Ops-Console / README: retire factory 36 h · 3-per-week · wait-for-score caps; point at Submit-Policy
- Architecture + Cowork wiki: **record-keeping cadence before/after** (loop v1 calendar vs loop v2 event-driven / KEPT14 / z-gate / wake ledger); both versions kept visible
- Architecture wiki: **Gemma agent + Eval Gate harness** and **LangChain / LangGraph** Mermaid flows (named colored bands; course evidence stack marked not-in-zip)

### Fixed
- Architecture Mermaid: loop v2 node label no longer embeds `jobs[]` (GitHub parse error); quoted labels on cadence diagrams
- `factory/state-and-artifacts.md` — schemas/paths for loop state, append-only wake ledger, `results/` files, and the read-only climb scoreboard bridge
- Runbook "Current state (2026-11-20)": V8–V23 evaluated, V22 awaiting second paired run (J1), V24 tool-layer read-budget cap queued
- `results/`: gate runs v7–v9, v11 (V18–V23), V20 LB 0.13, W47 manual submission 0.17, V20 calibration row
- `SECURITY.md` — reporting path, no-secrets policy, trust boundaries
- Wiki [[Method-Card]] — one-page academic method (problem → gate → evidence)
- GitHub Actions CI — pytest on harness/guardrails/factory (supervisor suite ignored pending langgraph pin)
- Wiki [[Ops-Console]] — Claude Agent Ops Console as **main** demo UI (screens + deny list vs Cowork)
- Ops Console directional screenshots under `docs/wiki/assets/ops-console/`

### Fixed
- `harness/decision_rule.py`: `V8_HISTORY` now loads every V8 baseline row from `results/gate_runs.csv` (was hard-coded to 2 runs, so Δ was off by 0.33, e.g. V22 +2.0 instead of +1.67). Thresholds unchanged; regression tests reproduce the logged W46 V18 and W47 V22 decisions.

### Changed
- CreateSubmission made explicitly human-approved in runbook, `project-instructions.md`, `weekly-decision` skill, factory diagram and Cowork wiki
- `project-instructions.md`: wake read list, UTC cadence, skill order, submission contract
- Skills: valid Eval Gate source versions (never 4/10); V8 history now 3 runs; climb scoreboard read-only; no harness/contract edits in `build-candidate`
- README / Method-Card / Architecture / Cowork wiki: V20, V22–V24 status; loop v2 note
- `.claude/launch.json`: Streamlit config renamed as legacy (not the demo UI)
- README / Home: score SoT note (factory V8 **0.18** vs sibling climb tip ledger)
- README References: eval-over-generator thesis vs SWE-bench / ReAct
- Future-Work: tool-layer edit deadline labeled **hypothesis — not shipped**
- Requirements-Compliance: pinned golden/safety table + calibration tally
- Local-And-Streamlit: climb bridge explicitly read-only (page now marks Streamlit **not used for demos**)
- README / Home / Cowork / Demo-Script / SECURITY / factory-console point at Claude Ops Console as **main** UI
- Streamlit removed from demo docs, Sidebar, Quick start, and screenshot set (no app code changes)

## [1.0.0-beta.1] — 2026-11-20

First public beta of the NoiseGate product repo (aligned with CMU course tracker `1.0.0-beta.1` SemVer).

### Product

- Gemma 4 SuperAgent **V8** base configs in `product/superagent/` (public LB **0.18**).
- Reproducible ADK zip builder: `python product/build_submission.py` → `submission.zip`.
- Installable Python package `noisegate-gemma4-factory==1.0.0b1` (`pyproject.toml`; sdist + wheel on the GitHub Release).
- Wheel force-includes `factory/`, `results/`, `docs/`, `GOALS.md` so the Streamlit console works when installed from the package (not only from a git checkout).

### Factory & harness

- Claude Cowork runbook + Skills (`build-candidate` → `run-eval-gate` → `weekly-decision` → `record-score`).
- Paired 30-task Eval Gate vs V8 noise band (~±2.5 tasks); coded HOLD/SUBMIT in `harness/decision_rule.py`.
- Streamlit Ops Console (`:8765`) for query/replay/approve — **never** CreateSubmission.

### Docs

- README paper pitch + Figure-1 three-band Mermaid (factory / product / Ops-HITL colors + legends).
- GitHub Wiki SoT synced from `docs/wiki/` (Architecture, Home, Requirements, Demo, Future Work).

### Links

- [Wiki Home](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Home)
- [Architecture](https://github.com/khaosans/noisegate-gemma4-factory/wiki/Architecture)
- [Video](https://youtu.be/-EiKv_MafOY)
- [Ops Console](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW)

[1.0.0-beta.1]: https://github.com/khaosans/noisegate-gemma4-factory/releases/tag/v1.0.0-beta.1
