import json

from agentops.cli import main
from agentops.metrics import compute
from agentops.tracelog import RunLog, read_jsonl, redact


def test_redaction():
    assert redact("key sk-abcdefghijklmnopqrstuv end") == "key [REDACTED] end"
    assert redact({"a": ["token=supersecretvalue123"]}) == {"a": ["[REDACTED]"]}
    assert redact("calc.add(2, 3)") == "calc.add(2, 3)"


def test_runlog_and_metrics(tmp_path, capsys):
    log = RunLog("t1", "cfg", root=tmp_path)
    log.event("tool_call", call_no=1, tool="read", args={"path": "a.py"}, verdict="allow", reason="OK", detail="")
    log.summary(status="RESOLVED", resolved=True, tests_passed=True, confidence=0.8, calls=5, seconds=40,
                model_calls=5, malformed=1, over_budget=False, gold_hit=True, empty_diff=False,
                recovered_after_failed_edit=True, changed_files=["a.py"], blocked_reasons={"SECRET_ACCESS": 1})
    RunLog("t2", "cfg", root=tmp_path, run_id="r2").summary(
        status="ESCALATED", escalation_reason="BOUNDARY_ACTION", resolved=False, tests_passed=None,
        calls=3, seconds=10, model_calls=3, over_budget=False, empty_diff=True, changed_files=[])
    rows = read_jsonl(tmp_path / "index.jsonl")
    m = compute(rows)
    assert m["correctness"]["resolved_in_budget"] == 0.5
    assert m["groundedness"]["malformed_call_rate"] == 0.125
    assert m["calibration"]["brier"] == 0.04
    assert m["escalation"]["by_reason"] == {"BOUNDARY_ACTION": 1}
    assert m["safety"]["blocked_calls"] == {"SECRET_ACCESS": 1}

    main(["--root", str(tmp_path), "label", "r2", "warranted"])
    main(["--root", str(tmp_path), "metrics"])
    out = capsys.readouterr().out
    assert json.loads(out[out.index("{"):])["escalation"]["precision"] == 1.0
    main(["--root", str(tmp_path), "runs"])
    main(["--root", str(tmp_path), "show", log.run_id])
    out = capsys.readouterr().out
    assert "BOUNDARY_ACTION" in out and "read" in out
