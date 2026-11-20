# Product: the Gemma 4 SuperAgent

This is what we submit. The Kaggle notebook
[Gemma 4 SuperAgent](https://www.kaggle.com/code/souriyakhaosanga/gemma-4-superagent) writes a
`submission.zip` with four files; each notebook version is one candidate.

```
superagent/
├── agent.yaml               # agent definition + tool list
├── configs/sampling.yaml    # temperature, max_output_tokens, thinking_budget
├── eval_config.yaml         # max_tool_calls and runtime limits
└── prompts/system.md        # the call plan Gemma follows
```

## Base config: V8 (public score 0.18)

| Setting | Value |
|---|---|
| temperature | 0.2 |
| max_output_tokens | 4096 |
| thinking_budget | 1024 |
| max_tool_calls | 28 |

Call plan in `prompts/system.md`:
1. Calls 1–6: locate and read the relevant code.
2. **Mandatory `edit_file` by call 7.**
3. From call 19: freeze exploration; only `git diff`, fix syntax, `submit_patch`.
4. Call 20: if the diff is still empty, make a minimal best-guess edit so `patch_size > 0`.

Known quirk: three graph tools (`get_code_neighbors`, `search_similar_code`, `get_code_subgraph`)
are declared in `agent.yaml` but forbidden by the prompt. See `candidates.md` (V16) and
`docs/decisions/` for why we test their removal one change at a time.

## Build

```bash
python product/build_submission.py     # writes submission.zip, prints per-file and zip SHA-256
```

Per-file hashes are what to compare against a Kaggle version's FILES; the zip hash only matches
the notebook's own zip writer.

### V8 hashes (repo export, fixed-timestamp zip)

| File | SHA-256 |
|---|---|
| `agent.yaml` | `680799291cc7d156d06fb7bfb5577f683ccc0d555b00e8ddb662d577f9bfa5e4` |
| `configs/sampling.yaml` | `770603e304a1639fc19b1ed61fceaf34ee415e9dbbe0fd4ab65bf96369fe021f` |
| `eval_config.yaml` | `916cf6cb34a6cc3de39837fa72cac681599b9ac2a3ee0b893adadfd36474c531` |
| `prompts/system.md` | `fb3bfe9d43f9f59e03b2d608b7a3c623ff2523948cf544f80bb4dafda5307ffb` |
| `submission.zip` (repo builder) | `217035630b660ffee837562c2d3806b7315762114fcd7cbe88d123687f2398af` |

## Exporting the files from Kaggle

The files in `superagent/` are exported verbatim from SuperAgent version 8 (run 362553010).
Open that version, copy the `FILES` dict from its code cells, and write each entry to the matching
path. Do not copy the competition's data, model weights, or other teams' notebooks into this repo.
