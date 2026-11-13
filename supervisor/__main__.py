"""Run one task:  python -m supervisor --task evals/fixtures/tinycalc/task.json [--hitl]"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .graph import Supervisor, Task
from .llm import make_chat_model
from .tools import resolve_sandbox


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True, help="JSON file with task_id, repo, issue, test_cmd")
    ap.add_argument("--model", default=None)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--config-name", default="supervisor-v1")
    ap.add_argument("--hitl", action="store_true", help="pause for a human on escalation")
    ap.add_argument("--unsafe-no-sandbox", action="store_true",
                    help="drive a live model with no OS sandbox (NOISEGATE_SANDBOX=local). The model's "
                         "shell and test commands can then reach the network and your files.")
    a = ap.parse_args()

    if resolve_sandbox() == "local" and not a.unsafe_no_sandbox:
        raise SystemExit(
            "Refusing to run a live model without an OS sandbox (NOISEGATE_SANDBOX=local).\n"
            "Use the default on macOS (seatbelt), set NOISEGATE_SANDBOX=docker, or pass "
            "--unsafe-no-sandbox if this machine is disposable.")
    spec = json.loads(Path(a.task).read_text())
    repo = Path(spec["repo"])
    if not repo.is_absolute():
        spec["repo"] = str((Path(a.task).parent / repo).resolve())
    task = Task(**spec)
    model = make_chat_model(a.model, a.base_url)
    sup = Supervisor(model, task, config_name=a.config_name, model_name=a.model, hitl=a.hitl)
    try:
        print(f"sandbox: {sup.rt.ws.sandbox}")
        res = sup.run()
        while res["status"] == "AWAITING_HUMAN":
            print(json.dumps(res["escalation"], indent=2))
            d = input("approve / deny? ").strip().lower() or "deny"
            res = sup.resume(d)
        print(json.dumps(res, indent=2, default=str))
        print(sup.diff() or "(no diff)")
    finally:
        sup.close()


if __name__ == "__main__":
    main()
