"""Factory console: actions over the repo's records, the offline operator, and the Claude tool loop."""
import json
import shutil
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from factory_console import actions
from factory_console.chat import (
    TOOLS, HANDLERS, ClaudeOperator, OfflineOperator, OllamaOperator,
    make_operator, openai_tools_from_anthropic, resolve_ollama_model,
)


def test_status_reports_state_and_stale_records():
    s = actions.status(today="2026-11-16")
    assert s["best_version"] == "V8" and s["best_public_score"] == 0.18
    assert s["days_to_deadline"] == 16 and s["held"] == ["V14", "V16", "V17"]
    assert s["due_today"].startswith("Monday")
    assert any("No gate run recorded" in w for w in s["warnings"])
    assert any("2026-11-09" in w for w in s["warnings"])


def test_records_parse():
    assert [c["version"] for c in actions.candidates()][:2] == ["V8", "V11"]
    assert actions.queue()[0]["position"] == 1 and len(actions.queue()) == 7
    assert len(actions.decisions()) == 7 and "Roll back" in actions.decisions(4)[0]["text"]
    assert actions.noise()["same_config_in_budget_solves"]["V15"] == {"runs": [7, 10], "spread": 3}
    assert actions.log_entries("V17 HOLD", 1)[0]["date"] == "2026-10-31"


def test_replay_decision_uses_the_candidates_own_baseline():
    r = actions.replay_decision("v17")
    assert r["base"] == "V15" and r["baseline_in_budget"] == [7, 10] and r["candidate_in_budget"] == [7]
    assert r["verdict"] == "HOLD" and r["delta"] == -1.5 and r["paired_net"] == -3
    assert "V15" in r["reasons"][0]
    assert "error" in actions.replay_decision("V99")


def test_what_if_matches_the_rule():
    assert actions.what_if([9, 8], 1)["verdict"] == "SUBMIT tier 2"
    assert actions.what_if([9, 8], -1)["verdict"] == "HOLD"
    assert actions.what_if([9], None)["verdict"] == "HOLD"
    assert "edited test files" in actions.what_if([12, 12], 3, test_file_edits=True)["reasons"]


def test_judge_sample_log_is_flagged_synthetic_and_not_mixed_with_30_task_history():
    r = actions.judge_gate_log()
    assert r["synthetic_sample"] and r["tasks_per_candidate"] == 8
    assert r["in_budget"] == {"C1": 5, "V8": 4} and r["paired_net"] == 1 and r["delta"] == 1
    assert r["verdict"] == "HOLD"  # one run is never enough
    assert "error" in actions.judge_gate_log("no score lines here")


def test_every_tool_has_a_handler():
    names = {t["name"] for t in TOOLS}
    assert names - {"record_score"} == set(HANDLERS)


def test_offline_operator_routes_and_never_writes():
    op = OfflineOperator()
    assert "HOLD" in op.ask("why was V17 held?").text
    assert "SUBMIT tier 2" in op.ask("what if 9 8 net 1").text
    assert "0.18" in op.ask("status").text
    assert "did not recognise" in op.ask("hello there").text


class FakeMessages:
    """Scripted Anthropic responses: one tool round, then a final answer."""

    def __init__(self, script):
        self.script, self.requests = list(script), []

    def create(self, **kw):
        self.requests.append({**kw, "messages": list(kw["messages"])})
        return self.script.pop(0)


def _resp(stop, *blocks):
    return SimpleNamespace(stop_reason=stop, content=list(blocks))


def _operator(script):
    pytest.importorskip("anthropic")
    import anthropic

    op = object.__new__(ClaudeOperator)
    op._anthropic, op.model, op.messages = anthropic, "test-model", []
    op.client = SimpleNamespace(beta=SimpleNamespace(messages=FakeMessages(script)))
    return op


def test_claude_loop_runs_tools_and_queues_writes_for_a_human():
    use = lambda i, name, inp: SimpleNamespace(type="tool_use", id=i, name=name, input=inp)
    op = _operator([
        _resp("tool_use", use("t1", "explain_candidate", {"version": "V17"}),
              use("t2", "record_score", {"version": "V18", "public_score": 0.19})),
        _resp("end_turn", SimpleNamespace(type="text", text="V17 was held.")),
    ])
    before = actions.leaderboard()
    reply = op.ask("why was V17 held, and record V18 at 0.19")
    assert reply.text == "V17 was held." and [s["name"] for s in reply.steps] == ["explain_candidate", "record_score"]
    assert reply.pending == [{"action": "record_score", "args": {"version": "V18", "public_score": 0.19}}]
    assert actions.leaderboard() == before  # nothing written without approval
    results = op.messages[2]["content"]     # both results go back in ONE user message
    assert [r["tool_use_id"] for r in results] == ["t1", "t2"] and '"verdict": "HOLD"' in results[0]["content"]
    assert op.client.beta.messages.requests[0]["tools"] == TOOLS


def test_record_score_appends_only_new_versions(tmp_path, monkeypatch):
    shutil.copytree(actions.ROOT / "results", tmp_path / "results")
    monkeypatch.setattr(actions, "ROOT", tmp_path)
    assert "error" in actions.record_score("V8", 0.2)
    out = actions.record_score("V18", 0.19, change="V8 + heredoc recovery")
    assert out["recorded"] and out["previous_best"] == 0.18
    assert actions.leaderboard()[-1]["version"] == "V18"
    assert "V18 scored 0.19" in (tmp_path / "results" / "eval-results.md").read_text()


def test_openai_tools_match_anthropic_names():
    converted = openai_tools_from_anthropic()
    assert {t["function"]["name"] for t in converted} == {t["name"] for t in TOOLS}
    assert all(t["type"] == "function" for t in converted)


def test_resolve_ollama_model_prefers_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
    with patch("factory_console.chat.ollama_models", return_value=["mistral:latest", "llama3.2:3b"]):
        assert resolve_ollama_model() == "llama3.2:3b"
    with patch("factory_console.chat.ollama_models", return_value=[]):
        assert resolve_ollama_model() is None


def test_make_operator_honors_backend_env(monkeypatch):
    monkeypatch.setenv("FACTORY_CONSOLE_BACKEND", "offline")
    assert isinstance(make_operator(), OfflineOperator)
    monkeypatch.setenv("FACTORY_CONSOLE_BACKEND", "ollama")
    with patch("factory_console.chat.ollama_models", return_value=["llama3.2:3b"]):
        op = make_operator()
        assert isinstance(op, OllamaOperator) and op.model == "llama3.2:3b"


def test_ollama_loop_runs_tools(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
    script = [
        {"choices": [{"finish_reason": "tool_calls", "message": {
            "role": "assistant", "content": "",
            "tool_calls": [{"id": "c1", "type": "function",
                            "function": {"name": "explain_candidate",
                                         "arguments": json.dumps({"version": "V17"})}}],
        }}]},
        {"choices": [{"finish_reason": "stop", "message": {
            "role": "assistant", "content": "V17 was held.",
        }}]},
    ]

    def fake_post(path, payload, timeout=120.0):
        assert path == "/v1/chat/completions"
        assert payload["model"] == "llama3.2:3b" and payload["tools"]
        return script.pop(0)

    with patch("factory_console.chat.ollama_models", return_value=["llama3.2:3b"]), \
         patch("factory_console.chat._ollama_post", side_effect=fake_post):
        op = OllamaOperator()
        reply = op.ask("why was V17 held?")
    assert reply.text == "V17 was held." and reply.mode == "ollama"
    assert [s["name"] for s in reply.steps] == ["explain_candidate"]
    assert '"verdict": "HOLD"' in json.dumps(reply.steps[0]["result"])


def test_ollama_operator_errors_clearly_when_down(monkeypatch):
    with patch("factory_console.chat.ollama_models", return_value=[]):
        with pytest.raises(RuntimeError, match="Ollama is not reachable"):
            OllamaOperator()


def test_ollama_parses_json_tool_call_in_content(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")
    script = [
        {"choices": [{"finish_reason": "stop", "message": {
            "role": "assistant",
            "content": json.dumps({"name": "factory_status", "parameters": {}}),
        }}]},
        {"choices": [{"finish_reason": "stop", "message": {
            "role": "assistant", "content": "Base V8, best 0.18.",
        }}]},
    ]
    with patch("factory_console.chat.ollama_models", return_value=["llama3.2:3b"]), \
         patch("factory_console.chat._ollama_post", side_effect=lambda *a, **k: script.pop(0)):
        reply = OllamaOperator().ask("status?")
    assert reply.steps[0]["name"] == "factory_status"
    assert reply.text == "Base V8, best 0.18."
