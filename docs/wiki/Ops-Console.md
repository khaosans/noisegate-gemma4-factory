# Ops Console (Claude artifact)

**Live UI:** [claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW)

Paper / **replay** console for demos and the class narrative. It illustrates factory state, gate HOLD insight, and human approval — it is **not** the climb runtime and **never** CreateSubmission.

Prefer linking out (do not iframe claude.ai in README — auth / embed fragility). Artifact URLs can drift; keep this page as the in-repo SoT for *what the Ops Console means*.

## Role in the system

Three operator surfaces — pick the right one:

| Surface | How | Data | CreateSubmission / gate-start? |
|---------|-----|------|--------------------------------|
| **React Ops Console** (this page) | Claude artifact | Paper / **replay** of recorded runs | **No** |
| **Streamlit** | `streamlit run factory_console/app.py --server.port 8765` | Live repo `results/` (+ optional climb **read-only** bridge) | **No** |
| **Claude Cowork** | Project + Skills + runbook | Authenticated Kaggle session | **Human only** |

```mermaid
flowchart LR
  subgraph Demo["Demo / paper"]
    React[React Ops Console artifact]
    ST[Streamlit :8765]
  end

  subgraph Climb["Climb ops"]
    CW[Claude Cowork + Skills]
  end

  React -.->|illustrates| Gate[Eval gate + HOLD]
  ST -->|reads| Results[results/ CSV + ledger]
  CW -->|auth session| Kaggle[Gate start / CreateSubmission HITL]
  Results -.->|may lag artifact| React
```

## What you can show

- Factory loop story: one delta → paired gate → **HOLD** inside noise  
- Human approval before costly ledger writes (HITL narrative)  
- Separation of product (Gemma ReAct) vs factory governance  
- Backup demo when Streamlit is down (open the artifact + walk HOLD)

## What you cannot claim

- Live leaderboard scrape or invented `publicScore`  
- Starting a Kaggle Eval Gate from the artifact  
- CreateSubmission or changing the base config  
- That artifact numbers are fresher than `results/*.csv` (they may **lag**)  
- That this UI replaces Cowork for login-heavy climb work  

Scores only count when they appear in `results/` / climb SoT — never invent them from the paper UI.

## Relation to the in-repo Streamlit console

| Concern | Docs |
|---------|------|
| Pages, chat backends, Approve flow | [`docs/factory-console.md`](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/docs/factory-console.md) |
| May / must-not + climb bridge | [[Local-And-Streamlit]] |
| Primary climb path | [[Claude-Cowork-Loop]] |
| Architecture bands | [[Architecture]] · [[Method-Card]] |

Streamlit is the **local query/demo** surface over the same factory concepts the React Ops Console presents for paper/demo. Same deny list: no gate-start, no submit.

## When to open which (operator cheat sheet)

| Goal | Open |
|------|------|
| Class talk / portfolio without Mac Streamlit | **React Ops Console** artifact |
| Query live CSVs, replay `decide()`, Approve `record_score`, pytest/zip | **Streamlit** `:8765` |
| Build candidate, start Eval Gate, CreateSubmission | **Cowork** (human) |

## Demo (60 seconds)

1. Open the [Ops Console artifact](https://claude.ai/artifact/6R7YzcGjHzh3U6dreF9YsW).  
2. Point at factory loop / a HOLD above the V8 noise band.  
3. Say: “Consoles never CreateSubmission — humans / Cowork own that.”  
4. Optional: contrast with Streamlit for “same story, live files.”

Full talk track: [[Demo-Script]].

## Maintaining the artifact

1. After meaningful `results/` or runbook changes, refresh the Claude artifact (or note lag on this page).  
2. Update this wiki page if the **role** or deny-list changes — not for every cosmetic UI tweak.  
3. After merging docs to `main`, sync GitHub Wiki from `docs/wiki/`.  
4. Optional later: archive a static export under `docs/ops-console/` if the claude.ai URL breaks (out of scope for this pass).

## Security / trust

See [`SECURITY.md`](https://github.com/khaosans/noisegate-gemma4-factory/blob/main/SECURITY.md). Artifact = demo-only; no secrets in screenshots or pasted logs.
