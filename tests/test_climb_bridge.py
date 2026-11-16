"""Climb / Kaggle bridge: fixture scoreboard only (no network)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from factory_console import climb_bridge
from factory_console.chat import OfflineOperator, TOOLS, HANDLERS

FIXTURE = Path(__file__).parent / "fixtures" / "climb_scoreboard.json"


@pytest.fixture
def climb_checkout(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    shutil.copy(FIXTURE, docs / "scoreboard.json")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "refresh_scoreboard.py").write_text(
        "raise SystemExit('refresh should be mocked in tests')\n", encoding="utf-8")
    return tmp_path


def test_missing_cmu_root_returns_clear_error(monkeypatch):
    monkeypatch.delenv("CMU_AGENTIC_AI_ROOT", raising=False)
    err = climb_bridge.climb_root()
    assert isinstance(err, dict) and "CMU_AGENTIC_AI_ROOT" in err["error"]
    board = climb_bridge.read_scoreboard()
    assert "error" in board and "CMU_AGENTIC_AI_ROOT" in board["error"]
    # Console status still works; climb slice carries the error.
    from factory_console import actions
    dual = climb_bridge.dual_status(actions.status(today="2026-11-16"))
    assert dual["best_public_score"] == 0.18
    assert "error" in dual["climb"]
    assert dual["score_mismatch"] is False
    assert "unavailable" in dual["sources"]["climb_board"]


def test_read_scoreboard_from_fixture(climb_checkout, monkeypatch):
    monkeypatch.setenv("CMU_AGENTIC_AI_ROOT", str(climb_checkout))
    board = climb_bridge.read_scoreboard()
    assert board["ok"] and board["best_public_score"] == 0.10
    assert board["best_public_score_ref"] == "57112729"
    assert board["pending_submit_utc"] == "2026-10-27T21:37:16Z"
    assert board["tip_git_commit"] == "abc123fixture"
    assert board["tip_hypothesis"]["profile"] == "shipcontract"
    hist = board["history_summary"]
    assert hist["pending_count"] == 1 and hist["complete_count"] == 1
    assert hist["pending"][0]["ref"] == "57401384"


def test_dual_status_flags_score_mismatch(climb_checkout, monkeypatch):
    monkeypatch.setenv("CMU_AGENTIC_AI_ROOT", str(climb_checkout))
    factory = {"best_public_score": 0.18, "best_version": "V8", "warnings": []}
    dual = climb_bridge.dual_status(factory)
    assert dual["score_mismatch"] is True
    assert dual["climb"]["best_public_score"] == 0.10
    assert dual["sources"]["factory_csv"] == "results/leaderboard.csv"
    assert any("0.18" in w and "0.1" in w for w in dual["warnings"])


def test_refresh_skipped_unless_env(climb_checkout, monkeypatch):
    monkeypatch.setenv("CMU_AGENTIC_AI_ROOT", str(climb_checkout))
    monkeypatch.delenv("FACTORY_CLIMB_REFRESH", raising=False)
    out = climb_bridge.refresh_and_read()
    assert out["refresh_requested"] is False and out["refreshed"] is False
    assert out["best_public_score"] == 0.10


def test_refresh_runs_script_when_env_set(climb_checkout, monkeypatch):
    monkeypatch.setenv("CMU_AGENTIC_AI_ROOT", str(climb_checkout))
    monkeypatch.setenv("FACTORY_CLIMB_REFRESH", "1")
    script = climb_checkout / "scripts" / "refresh_scoreboard.py"
    script.write_text(
        "from pathlib import Path\n"
        "import json\n"
        "p = Path('docs/scoreboard.json')\n"
        "d = json.loads(p.read_text())\n"
        "d['best_public_score'] = 0.12\n"
        "d['best_public_score_ref'] = 'refreshed'\n"
        "p.write_text(json.dumps(d))\n"
        "print('ok')\n",
        encoding="utf-8",
    )
    out = climb_bridge.refresh_and_read()
    assert out["refreshed"] is True and out["best_public_score"] == 0.12
    snap = climb_bridge.kaggle_submissions_snapshot()
    assert snap["ok"] and snap["refreshed"] is True
    assert snap["counts"]["PENDING"] == 1
    assert snap["pending"][0]["ref"] == "57401384"


def test_refresh_failure_surfaces_stderr(climb_checkout, monkeypatch):
    monkeypatch.setenv("CMU_AGENTIC_AI_ROOT", str(climb_checkout))
    monkeypatch.setenv("FACTORY_CLIMB_REFRESH", "1")
    (climb_checkout / "scripts" / "refresh_scoreboard.py").write_text(
        "import sys\nprint('boom-stderr', file=sys.stderr)\nraise SystemExit(2)\n",
        encoding="utf-8",
    )
    out = climb_bridge.refresh_and_read()
    assert "error" in out and out["refresh_returncode"] == 2
    assert "boom-stderr" in (out.get("refresh_stderr_tail") or "")


def test_tools_include_climb_handlers():
    names = {t["name"] for t in TOOLS}
    assert {"climb_scoreboard", "kaggle_submissions_snapshot"} <= names
    assert names - {"record_score"} == set(HANDLERS)


def test_offline_keywords_climb_kaggle_pending(climb_checkout, monkeypatch):
    monkeypatch.setenv("CMU_AGENTIC_AI_ROOT", str(climb_checkout))
    op = OfflineOperator()
    climb = op.ask("climb scoreboard?")
    assert "0.1" in climb.text and "57112729" in climb.text
    pending = op.ask("any kaggle pending?")
    assert "PENDING" in pending.text and "57401384" in pending.text
    status = op.ask("where does the factory stand?")
    assert "score_mismatch" in status.text or "0.18" in status.text
