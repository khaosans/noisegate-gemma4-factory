"""AgentOps CLI over the JSONL run logs.

  python -m agentops runs [--status ESCALATED] [--last 20]   list runs
  python -m agentops show RUN_ID                             step-by-step trace of one run
  python -m agentops metrics [--config NAME]                 checkpoint 6.1 metrics
  python -m agentops label RUN_ID warranted|unwarranted      mark an escalation after review
  python -m agentops query "SELECT ..."                      SQL over views `runs` and `events` (needs duckdb)

Set NOISEGATE_RUNS_DIR to read another runs folder (default ./runs).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .metrics import compute
from .tracelog import default_root, read_jsonl


def _runs(root: Path) -> list[dict]:
    rows = read_jsonl(root / "index.jsonl")
    labels = {r["run_id"]: r["warranted"] for r in read_jsonl(root / "labels.jsonl")}
    for r in rows:
        if r["run_id"] in labels:
            r["escalation_warranted"] = labels[r["run_id"]]
    return rows


def cmd_runs(root: Path, a) -> None:
    rows = [r for r in _runs(root) if not a.status or r.get("status") == a.status][-a.last:]
    print(f"{'run_id':<24} {'task':<22} {'config':<16} {'status':<10} {'calls':>5} {'sec':>6}  reason")
    for r in rows:
        print(f"{r['run_id']:<24} {r['task_id'][:22]:<22} {r['config'][:16]:<16} {r.get('status',''):<10} "
              f"{r.get('calls',0):>5} {r.get('seconds',0):>6}  {r.get('escalation_reason') or ''}")


def cmd_show(root: Path, a) -> None:
    events = read_jsonl(root / "events" / f"{a.run_id}.jsonl")
    if not events:
        sys.exit(f"no events for {a.run_id}")
    for e in events:
        k = e["kind"]
        if k == "tool_call":
            line = f"call {e['call_no']:>2}  {e['tool']:<8} {e['verdict']:<8} {e['reason']:<22} {json.dumps(e['args'])[:90]}"
        elif k == "tool_result":
            line = f"         -> ok={e['ok']} {e['ms']} ms  {e['output'][:80]!r}"
        elif k == "model_call":
            line = f"model    {e['ms']} ms  {'ERROR ' + e['error'] if e.get('error') else ''}"
        elif k == "verify":
            line = f"verify   changed={e['changed']} tests_passed={e['tests_passed']} failures={e['failures']} flags={e['review_flags']}"
        elif k == "escalate":
            line = f"ESCALATE {e.get('reason')}: {str(e.get('detail'))[:100]}"
        else:
            line = f"{k:<8} " + json.dumps({x: y for x, y in e.items() if x not in ('ts', 'run_id', 'task_id', 'config', 'seq', 'kind')})[:120]
        print(f"{e['seq']:>3} {line}")


def cmd_metrics(root: Path, a) -> None:
    rows = [r for r in _runs(root) if not a.config or r.get("config") == a.config]
    print(json.dumps(compute(rows), indent=2))


def cmd_label(root: Path, a) -> None:
    root.mkdir(parents=True, exist_ok=True)
    with (root / "labels.jsonl").open("a") as f:
        f.write(json.dumps({"run_id": a.run_id, "warranted": a.verdict == "warranted"}) + "\n")
    print(f"labelled {a.run_id}: {a.verdict}")


def cmd_query(root: Path, a) -> None:
    try:
        import duckdb
    except ImportError:
        sys.exit("query needs duckdb: pip install duckdb")
    con = duckdb.connect()
    con.execute(f"CREATE VIEW runs AS SELECT * FROM read_json_auto('{root / 'index.jsonl'}')")
    con.execute(f"CREATE VIEW events AS SELECT * FROM read_json_auto('{root / 'events'}/*.jsonl', union_by_name=true)")
    print(con.sql(a.sql))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="agentops", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=None, help="runs folder (default $NOISEGATE_RUNS_DIR or ./runs)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("runs"); p.add_argument("--status"); p.add_argument("--last", type=int, default=20)
    p = sub.add_parser("show"); p.add_argument("run_id")
    p = sub.add_parser("metrics"); p.add_argument("--config")
    p = sub.add_parser("label"); p.add_argument("run_id"); p.add_argument("verdict", choices=["warranted", "unwarranted"])
    p = sub.add_parser("query"); p.add_argument("sql")
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else default_root()
    {"runs": cmd_runs, "show": cmd_show, "metrics": cmd_metrics, "label": cmd_label, "query": cmd_query}[a.cmd](root, a)


if __name__ == "__main__":
    main()
