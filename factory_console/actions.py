"""The factory's operator actions: everything the console (chat or UI) is allowed to do.

Three groups, all plain functions that return JSON-friendly dicts:

  query   read the factory's records (gate runs, leaderboard, queue, decisions, run logs)
  check   apply the factory's own rules to those records (decision rule, runbook, goals)
  run     execute local, bounded jobs (tests, safety eval, zip build, one supervised agent run)

What is deliberately NOT here: starting a Kaggle gate run, submitting to the leaderboard, and
changing the base config. The runbook reserves those for humans. `record_score` writes to the
results files and is only ever called after a human approves it in the UI.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from statistics import mean
from typing import Any, Optional

from agentops.metrics import compute as compute_metrics
from agentops.tracelog import read_jsonl
from harness.decision_rule import V8_HISTORY, RunSummary, decide, paired_net
from harness.evaluators import scorecard
from harness.trajectory import parse_log

def _discover_root() -> Path:
    """Repo checkout or installed wheel data next to the import packages.

    Prefer ``NOISEGATE_ROOT``. Otherwise use a tree that has ``factory/runbook.md``
    (checkout or hatch force-include into site-packages). Falls back to the
    parent of ``factory_console/`` so local editable installs keep working.
    """
    env = (os.environ.get("NOISEGATE_ROOT") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve().parent
    for candidate in (here.parent, *here.parents):
        if (candidate / "factory" / "runbook.md").is_file():
            return candidate
    return here.parent


ROOT = _discover_root()
SAMPLE_LOG = Path(__file__).with_name("sample_gate_log.txt")
GATE_NOISE_TASKS = 3      # same config moved by up to 3 in-budget solves between runs
LEADERBOARD_NOISE = 0.05  # an identical public 0.22 config scored 0.17


def _runs_root() -> Path:
    return Path(os.environ.get("NOISEGATE_RUNS_DIR") or ROOT / "runs")


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _csv(rel: str) -> list[dict]:
    with (ROOT / rel).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _int(v: Any) -> Optional[int]:
    return None if v in (None, "") else int(v)


def _today(today: str | None = None) -> dt.date:
    return dt.date.fromisoformat(today) if today else dt.datetime.now(dt.timezone.utc).date()


# ----------------------------------------------------------------------------- query

def gate_runs() -> list[dict]:
    """Every Eval Gate row (one per candidate per run). Counts are per 30 tasks."""
    ints = ("solved", "in_budget", "empty_diff", "edit_fail", "logic_mismatch", "timeout",
            "over_28_calls", "paired_net_vs_baseline")
    return [{**r, **{k: _int(r[k]) for k in ints}} for r in _csv("results/gate_runs.csv")]


def leaderboard() -> list[dict]:
    return [{**r, "public_score": float(r["public_score"])} for r in _csv("results/leaderboard.csv")]


def candidates() -> list[dict]:
    """The candidate table from product/candidates.md."""
    rows = []
    for line in _read("product/candidates.md").splitlines():
        cells = [re.sub(r"\*\*|\[([^\]]*)\]\([^)]*\)", r"\1", c).strip() for c in line.strip().strip("|").split("|")]
        if re.match(r"\| V\d", line) and len(cells) == 5:
            rows.append(dict(zip(("version", "base", "change", "gate", "leaderboard"), cells)))
    return rows


def queue() -> list[dict]:
    """The ordered candidate queue (each item is the base plus exactly one change)."""
    text = _read("product/candidates.md").split("## Queue", 1)[-1]
    return [{"position": int(m.group(1)), "change": m.group(2).strip()}
            for m in re.finditer(r"^(\d+)\.\s+(.*)$", text, re.M)]


def decisions(number: int | None = None) -> list[dict]:
    """Decision records. Without a number: titles and status. With one: the full text."""
    out = []
    for p in sorted((ROOT / "docs" / "decisions").glob("*.md")):
        n = int(p.name[:3])
        text = p.read_text(encoding="utf-8")
        status = re.search(r"\*\*Status:\*\*\s*(.*)", text)
        rec = {"number": n, "title": text.splitlines()[0].lstrip("# ").strip(),
               "status": status.group(1).strip() if status else ""}
        if number is not None:
            if n != number:
                continue
            rec["text"] = text
        out.append(rec)
    return out


def lessons() -> str:
    return _read("docs/lessons.md")


def log_entries(query: str | None = None, limit: int = 5) -> list[dict]:
    """Dated entries from results/eval-results.md, newest first, optionally filtered by text."""
    parts = re.split(r"^## ", _read("results/eval-results.md"), flags=re.M)[1:]
    entries = [{"title": p.splitlines()[0].strip(), "text": p.strip(),
                "date": (re.match(r"\d{4}-\d\d-\d\d", p) or [""])[0]} for p in parts]
    if query:
        words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 1]
        entries = [e for e in entries if all(w in e["text"].lower() for w in words)]
    return entries[::-1][:limit]


def noise() -> dict:
    """How far the same config moves between runs: the reason single comparisons are not trusted."""
    by: dict[str, list[int]] = {}
    for r in gate_runs():
        if r["candidate"] == r["baseline"]:
            by.setdefault(r["candidate"], []).append(r["in_budget"])
    return {
        "same_config_in_budget_solves": {k: {"runs": v, "spread": max(v) - min(v)} for k, v in by.items()},
        "gate_noise_tasks_per_30": GATE_NOISE_TASKS,
        "leaderboard_noise": LEADERBOARD_NOISE,
        "leaderboard_evidence": "V15 is an exact copy of a public 0.22 config and scored 0.17 for us.",
    }


# ----------------------------------------------------------------------------- check

def _summary(row: dict) -> RunSummary:
    # gate_runs.csv has no time-overrun or non-source column, so these are the call-count and
    # EMPTY_DIFF counts only. Close to, but not exactly, what the notebook feeds the rule.
    return RunSummary(in_budget_solves=row["in_budget"], empty_or_nonsource=row["empty_diff"],
                      overruns=row["over_28_calls"])


def replay_decision(version: str) -> dict:
    """Re-apply today's decision rule (decision 005) to a recorded candidate.

    The baseline is the config the candidate was built on (V8 or V15), using every recorded run
    of that baseline. Verdicts recorded at the time used earlier versions of the rule, so the
    recorded verdict and this replay can differ in wording; both are returned.
    """
    version = version.upper()
    rows = [r for r in gate_runs() if r["candidate"] == version and r["baseline"] != version]
    if not rows:
        known = sorted({r["candidate"] for r in gate_runs() if r["candidate"] != r["baseline"]})
        return {"error": f"{version} has no candidate rows in results/gate_runs.csv", "candidates": known}
    base = rows[-1]["baseline"]
    base_rows = [r for r in gate_runs() if r["candidate"] == base]
    scored = {r["version"] for r in leaderboard()}
    net = rows[-1]["paired_net_vs_baseline"]
    d = decide([_summary(r) for r in rows], [_summary(r) for r in base_rows], run_b_paired_net=net,
               zip_sha_ok=True, one_change_off_base=True, never_scored=version not in scored)
    change = next((c["change"] for c in candidates() if c["version"] == version), None)
    return {
        "version": version, "base": base, "the_one_change": change,
        "candidate_in_budget": [r["in_budget"] for r in rows],
        "baseline_in_budget": [r["in_budget"] for r in base_rows],
        "baseline_mean": round(mean(r["in_budget"] for r in base_rows), 2),
        "paired_net": net, "delta": d.delta, "verdict": d.verdict,
        "reasons": [x.replace("V8", base) for x in d.reasons],
        "recorded_verdict": rows[-1]["verdict"],
        "gate_rows": rows, "baseline_rows": base_rows,
        "bars": {"tier_2": 1.0, "tier_1": 2.5, "single_run": 4.0},
        "note": "Replay under the current rule; zip hash and one-change checks assumed true.",
    }


def what_if(in_budget_runs: list[int], paired_net_run_b: int | None = None, empty_per_run: float = 8,
            overruns_per_run: float = 17, test_file_edits: bool = False, harness_error: bool = False,
            zip_sha_ok: bool = True, one_change_off_base: bool = True, never_scored: bool = True,
            single_run_screen: bool = False) -> dict:
    """Run the decision rule on hypothetical numbers against V8's recorded history."""
    cand = [RunSummary(int(n), empty_per_run, overruns_per_run, harness_errors=int(harness_error),
                       test_file_edits=int(test_file_edits)) for n in in_budget_runs]
    if not cand:
        return {"error": "give at least one run's in-budget solves"}
    d = decide(cand, V8_HISTORY, paired_net_run_b, zip_sha_ok=zip_sha_ok,
               one_change_off_base=one_change_off_base, never_scored=never_scored,
               single_run_screen=single_run_screen)
    return {"verdict": d.verdict, "delta": d.delta, "reasons": d.reasons,
            "candidate_mean": round(mean(in_budget_runs), 2),
            "v8_mean": round(mean(r.in_budget_solves for r in V8_HISTORY), 2),
            "v8_runs": [r.in_budget_solves for r in V8_HISTORY]}


def judge_gate_log(text: str | None = None, candidate: str | None = None, baseline: str = "V8") -> dict:
    """Parse an Eval Gate log (or the bundled synthetic sample) and apply the rule to it."""
    sample = text is None
    rows = parse_log((text if text is not None else SAMPLE_LOG.read_text()).splitlines())
    if not rows:
        return {"error": "no 'Score' lines found; expected the Eval Gate v3 line format"}
    names = sorted({r.candidate for r in rows})
    candidate = candidate or next((n for n in names if n != baseline), names[0])
    cand = [r for r in rows if r.candidate == candidate]
    base = [r for r in rows if r.candidate == baseline]
    if not cand or not base:
        return {"error": f"need rows for both {candidate} and {baseline}", "candidates_in_log": names}
    # V8's recorded history is per 30 tasks, so it only joins a full 30-task run.
    history = (V8_HISTORY if baseline == "V8" and len(base) == 30 else []) + [RunSummary.from_results(base)]
    net = paired_net(cand, base)
    d = decide([RunSummary.from_results(cand)], history, run_b_paired_net=net,
               zip_sha_ok=True, one_change_off_base=True, never_scored=True)
    tasks = [{"candidate": r.candidate, "task": r.task, "mode": r.mode, "solved": r.solved,
              "calls": r.calls, "dur_s": r.dur_s, "first_edit": r.first_edit,
              "in_budget_solve": r.in_budget_solve} for r in cand + base]
    return {"synthetic_sample": sample, "candidate": candidate, "baseline": baseline,
            "tasks_per_candidate": len(cand),
            "in_budget": {candidate: sum(r.in_budget_solve for r in cand),
                          baseline: sum(r.in_budget_solve for r in base)},
            "paired_net": net, "verdict": d.verdict, "delta": d.delta, "reasons": d.reasons,
            "scorecard": scorecard(cand + base), "tasks": tasks}


WEEKDAY_JOBS = {
    5: "Saturday: build the top two untried queue items as C1 and C2, verify source and SHA-256, start Gate Run A.",
    6: "Sunday: pick the leader from Run A and start Gate Run B against V8.",
    0: "Monday: apply the decision rule. Submit only on a pass.",
}


def status(today: str | None = None) -> dict:
    """One-screen state of the factory, including what is stale or missing."""
    day = _today(today)
    runbook = _read("factory/runbook.md")
    deadline = dt.date.fromisoformat(re.search(r"Final deadline (\d{4}-\d\d-\d\d)", runbook).group(1))
    lb, runs = leaderboard(), gate_runs()
    best = max(lb, key=lambda r: r["public_score"])
    cands = [r for r in runs if r["candidate"] != r["baseline"]]
    held = sorted({r["candidate"] for r in cands if r["verdict"] == "HOLD"})
    last_run = max(r["date"] for r in runs)
    last_log = max((e["date"] for e in log_entries(limit=100) if e["date"]), default="")
    slots = [dt.date(deadline.year, 11, int(d)) for d in
             re.search(r"Planned submission slots: Nov ([\d, ]+)", runbook).group(1).replace(" ", "").split(",")]
    placeholders = [f for f in ("agent.yaml", "configs/sampling.yaml", "eval_config.yaml", "prompts/system.md")
                    if "TODO" in _read(f"product/superagent/{f}")]
    warnings = []
    stale = (day - dt.date.fromisoformat(last_run)).days
    if stale > 7:
        warnings.append(f"No gate run recorded for {stale} days (last: {last_run}).")
    missed = [s.isoformat() for s in slots if s < day and s.isoformat() > last_log]
    if missed:
        warnings.append(f"Planned submission slots with nothing recorded: {', '.join(missed)}.")
    if placeholders:
        warnings.append("product/superagent/ still holds TODO placeholders, not V8's exported files: "
                        + ", ".join(placeholders) + ".")
    if not (_runs_root() / "index.jsonl").exists():
        warnings.append("No supervisor run logs yet (runs/ is empty).")
    return {
        "today": day.isoformat(), "deadline": deadline.isoformat(), "days_to_deadline": (deadline - day).days,
        "base": "V8", "best_version": best["version"], "best_public_score": best["public_score"],
        "submissions_scored": len(lb), "gate_runs": len({r["gate_run"] for r in runs}),
        "candidates_gated": len({r["candidate"] for r in cands}), "held": held,
        "last_gate_run": last_run, "last_log_entry": last_log,
        "next_in_queue": queue()[:2], "next_submission_slots": [s.isoformat() for s in slots if s >= day],
        "due_today": WEEKDAY_JOBS.get(day.weekday(), "Status only: record new scores, refresh dashboards."),
        "warnings": warnings,
    }


def goals() -> list[dict]:
    rows, objective = [], ""
    for line in _read("GOALS.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == 3 and not set(cells[1]) <= set("-: ") and cells[1] != "Key result":
            objective = cells[0].strip("*") or objective
            rows.append({"objective": objective, "key_result": cells[1], "status": cells[2]})
    return rows


# ----------------------------------------------------------------------------- run

def _run(cmd: list[str], timeout: int, cwd: Path | None = None, tail: int | None = 4000) -> dict:
    try:
        p = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "PYTHONPATH": str(ROOT)})
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": None, "output": f"timed out after {timeout} s"}
    return {"ok": p.returncode == 0, "returncode": p.returncode,
            "output": (p.stdout + p.stderr).strip()[-tail:] if tail else p.stdout.strip()}


def run_tests() -> dict:
    """Run the repo's test suite (decision rule, parser, guardrails, supervisor, safety eval)."""
    res = _run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], timeout=600)
    tail = res["output"].splitlines()[-1] if res["output"] else ""
    return {**res, "summary": tail}


def run_safety_eval() -> dict:
    """Play the adversarial prompt-injection cases through the supervisor (scripted model)."""
    res = _run([sys.executable, "-m", "evals.safety.run", "--json",
                "--runs-dir", str(_runs_root() / "safety")], timeout=600, tail=None)
    try:
        data = json.loads(res["output"][res["output"].index("{"):])
        return {"ok": res["ok"], "summary": data.get("summary", data)}
    except (ValueError, json.JSONDecodeError):
        return {**res, "output": res["output"][-2000:]}


def build_submission() -> dict:
    """Rebuild submission.zip in a temp folder and report SHA-256 hashes. Submits nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        res = _run([sys.executable, str(ROOT / "product" / "build_submission.py")], timeout=60, cwd=Path(tmp))
    hashes = [dict(zip(("sha256", "file"), line.split())) for line in res["output"].splitlines()
              if len(line.split()) == 2]
    placeholder = status()["warnings"]
    return {"ok": res["ok"], "hashes": hashes, "submitted": False,
            "warning": next((w for w in placeholder if "placeholders" in w), None)}


SCRIPTED_CALLS = [
    {"tool": "read", "args": {"path": "calc.py"}},
    {"tool": "edit", "args": {"path": "tests/test_calc.py", "old": "== 5", "new": "== -1"}},
    {"tool": "edit", "args": {"path": "calc.py", "old": "return a - b", "new": "return a + b"}},
    {"tool": "test", "args": {}},
    {"tool": "submit", "args": {"confidence": 0.9, "summary": "add() returned a - b; now a + b"}},
]


def _supervise(model, model_name: str, config_name: str) -> dict:
    from supervisor.graph import Supervisor, Task

    fixture = ROOT / "evals" / "fixtures" / "tinycalc"
    spec = json.loads((fixture / "task.json").read_text())
    spec["repo"] = str(fixture)
    sup = Supervisor(model, Task(**spec), runs_dir=_runs_root(), config_name=config_name, model_name=model_name)
    try:
        res = sup.run()
        return {"run_id": sup.run_id, "status": res["status"], "diff": sup.diff(),
                "sandbox": sup.rt.ws.sandbox, "model": model_name, "config": config_name}
    finally:
        sup.close()


def run_scripted_agent() -> dict:
    """One supervised run on the tinycalc fixture with a SCRIPTED model (not Gemma).

    The script tries to edit a test file first, so the trace shows a guardrail block followed by
    the allowed source fix. It demonstrates the supervisor and the run log, not model quality.
    """
    from itertools import chain, repeat

    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage

    msgs = [AIMessage(content=json.dumps(c)) for c in SCRIPTED_CALLS]
    model = GenericFakeChatModel(messages=chain(msgs, repeat(msgs[-1])))
    return {**_supervise(model, "scripted", "scripted-demo"), "scripted": True}


def gemma_ready() -> dict:
    """Is a local model endpoint up, and does it serve the configured model tag?"""
    base = os.environ.get("NOISEGATE_BASE_URL", "http://localhost:11434/v1").rstrip("/")
    model = os.environ.get("NOISEGATE_MODEL", "")
    try:
        with urllib.request.urlopen(f"{base}/models", timeout=3) as r:
            served = [m["id"] for m in json.load(r).get("data", [])]
    except Exception as e:  # connection refused, timeout, bad JSON
        return {"ready": False, "base_url": base, "model": model, "why": f"endpoint not reachable: {e}"}
    if not model:
        return {"ready": False, "base_url": base, "served": served, "why": "NOISEGATE_MODEL is not set"}
    if model not in served:
        return {"ready": False, "base_url": base, "model": model, "served": served,
                "why": f"{model} is not served by this endpoint"}
    return {"ready": True, "base_url": base, "model": model}


def run_gemma_agent() -> dict:
    """One supervised run on the tinycalc fixture with the local model (NOISEGATE_MODEL)."""
    from supervisor.llm import make_chat_model
    from supervisor.tools import resolve_sandbox

    ready = gemma_ready()
    if not ready["ready"]:
        return {"error": "local model not ready", **ready}
    if resolve_sandbox() == "local":
        return {"error": "refusing to run a live model without an OS sandbox (NOISEGATE_SANDBOX=local)"}
    return _supervise(make_chat_model(), ready["model"], "supervisor-v1")


def agent_runs(last: int = 20) -> list[dict]:
    keep = ("run_id", "task_id", "config", "model", "status", "calls", "seconds", "tests_passed",
            "empty_diff", "over_budget", "first_edit_call", "blocked", "escalation_reason")
    return [{k: r.get(k) for k in keep} for r in read_jsonl(_runs_root() / "index.jsonl")[-last:]]


def agent_run(run_id: str) -> dict:
    """Step-by-step events of one supervised run."""
    if not re.fullmatch(r"[\w\-]+", run_id):
        return {"error": "bad run id"}
    events = read_jsonl(_runs_root() / "events" / f"{run_id}.jsonl")
    if not events:
        return {"error": f"no events for {run_id}"}
    return {"run_id": run_id, "events": events}


def agent_metrics(config: str | None = None) -> dict:
    rows = [r for r in read_jsonl(_runs_root() / "index.jsonl") if not config or r.get("config") == config]
    return compute_metrics(rows)


def record_score(version: str, public_score: float, kaggle_run_id: str = "", submitted_utc: str = "",
                 change: str = "", notes: str = "") -> dict:
    """Append a leaderboard score to results/. Call only after a human approved it."""
    version = version.upper()
    if not re.fullmatch(r"V\d+", version) or not 0 <= public_score <= 1:
        return {"error": "need a version like V18 and a score between 0 and 1"}
    if version in {r["version"] for r in leaderboard()}:
        return {"error": f"{version} is already in results/leaderboard.csv"}
    best = max(r["public_score"] for r in leaderboard())
    with (ROOT / "results" / "leaderboard.csv").open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([version, kaggle_run_id, submitted_utc or "TBD", public_score, change, notes])
    day = _today().isoformat()
    verdict = ("at or above the best, so it becomes the base (human decision to confirm)"
               if public_score >= best else f"below the best ({best}); base unchanged")
    with (ROOT / "results" / "eval-results.md").open("a", encoding="utf-8") as f:
        f.write(f"\n## {day} — {version} scored {public_score}\n"
                f"- {version} scored **{public_score}** on the public leaderboard: {verdict}.\n"
                f"- Recorded from the factory console. Calibration row and GOALS.md status still to update.\n")
    return {"recorded": True, "version": version, "public_score": public_score, "previous_best": best,
            "still_to_do": ["calibration row in results/README.md", "status column in GOALS.md"]}
