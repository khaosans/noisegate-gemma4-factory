# Changelog

All notable changes to NoiseGate Gemma 4 Factory are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning is Capstone **beta SemVer** (`X.Y.Z-beta.N`) until an explicit human GA cut.

## [Unreleased]

### Added
- `SECURITY.md` — reporting path, no-secrets policy, trust boundaries
- Wiki [[Method-Card]] — one-page academic method (problem → gate → evidence)
- GitHub Actions CI — pytest on harness/guardrails/factory (supervisor suite ignored pending langgraph pin)
- Wiki [[Ops-Console]] — Claude artifact paper/replay docs vs Streamlit vs Cowork
- Ops Console / Streamlit screenshots under `docs/wiki/assets/ops-console/`

### Changed
- README / Home: score SoT note (factory V8 **0.18** vs sibling climb tip ledger)
- README References: eval-over-generator thesis vs SWE-bench / ReAct
- Future-Work: tool-layer edit deadline labeled **hypothesis — not shipped**
- Requirements-Compliance: pinned golden/safety table + calibration tally
- Local-And-Streamlit: climb bridge explicitly read-only
- README / Home / Cowork / Local / factory-console / SECURITY cross-links to Ops Console docs
- Ops-Console framed as **default** demo/ops UI; Streamlit documented as **optional** and rough (docs only; no app code changes)
- Demo-Script / Home / README: lead with Claude Ops Console artifact; Streamlit secondary

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
