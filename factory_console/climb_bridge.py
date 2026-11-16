"""Read-only bridge from the factory console to cmu-agentic-ai climb / Kaggle SoT.

The climb checkout owns live Kaggle via `scripts/refresh_scoreboard.py` →
`docs/scoreboard.json`. This module only reads that board (and optionally runs the
refresh script). It never CreateSubmission, starts a gate, or writes NoiseGate CSVs.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCOREBOARD_REL = Path("docs") / "scoreboard.json"
REFRESH_SCRIPT_REL = Path("scripts") / "refresh_scoreboard.py"
REFRESH_ENV = "FACTORY_CLIMB_REFRESH"
ROOT_ENV = "CMU_AGENTIC_AI_ROOT"
REFRESH_TIMEOUT_S = 120


def climb_root() -> Path | dict:
    """Absolute path to the climb checkout, or an error dict if unset/missing."""
    raw = (os.environ.get(ROOT_ENV) or "").strip()
    if not raw:
        return {
            "error": f"{ROOT_ENV} is not set",
            "hint": "Point it at the absolute path of the cmu-agentic-ai checkout "
                    "(climb scoreboard + Kaggle refresh live there).",
        }
    root = Path(raw).expanduser()
    if not root.is_absolute():
        return {"error": f"{ROOT_ENV} must be an absolute path", "got": raw}
    if not root.is_dir():
        return {"error": f"{ROOT_ENV} is not a directory", "path": str(root)}
    return root.resolve()


def _scoreboard_path(root: Path) -> Path:
    return root / SCOREBOARD_REL


def _summarize_history(history: list[dict]) -> dict:
    """COMPLETE / PENDING (and ERROR) counts plus newest rows for chat."""
    by_status: dict[str, int] = {}
    for row in history:
        st = str(row.get("status") or "UNKNOWN").upper()
        by_status[st] = by_status.get(st, 0) + 1
    pending = [r for r in history if str(r.get("status") or "").upper() == "PENDING"]
    complete = [r for r in history if str(r.get("status") or "").upper() == "COMPLETE"]
    latest = history[-1] if history else None
    return {
        "counts": by_status,
        "pending_count": by_status.get("PENDING", 0),
        "complete_count": by_status.get("COMPLETE", 0),
        "latest": _slim_hist_row(latest) if latest else None,
        "pending": [_slim_hist_row(r) for r in pending],
        "recent_complete": [_slim_hist_row(r) for r in complete[-5:]],
    }


def _slim_hist_row(row: dict | None) -> dict | None:
    if not row:
        return None
    keep = ("ref", "status", "public_score", "submitted_utc", "message", "kernel",
            "kernel_version", "script_version_id", "author", "error")
    return {k: row.get(k) for k in keep if k in row or k in ("ref", "status", "public_score")}


def _board_slice(raw: dict) -> dict:
    """Fields the console needs: best public, latest/pending, tip pin."""
    history = list(raw.get("history") or [])
    tip = raw.get("tip_hypothesis")
    return {
        "ok": True,
        "best_public_score": raw.get("best_public_score"),
        "best_public_score_ref": raw.get("best_public_score_ref"),
        "best_public": raw.get("best_public"),
        "pending_submit_utc": raw.get("pending_submit_utc"),
        "last_submit_utc": raw.get("last_submit_utc"),
        "last_message": raw.get("last_message"),
        "pending_wait_it_out": raw.get("pending_wait_it_out"),
        "pending_queue_note": raw.get("pending_queue_note"),
        "tip_git_commit": raw.get("tip_git_commit"),
        "tip_hypothesis": tip if isinstance(tip, dict) else tip,
        "next_tip_plan": raw.get("next_tip_plan"),
        "history_summary": _summarize_history(history),
        "scoreboard_path": None,  # filled by caller
        "refreshed": False,
    }


def read_scoreboard(root: Path | None = None) -> dict:
    """Parse climb `docs/scoreboard.json`. Never invents scores."""
    resolved = root if isinstance(root, Path) else climb_root()
    if isinstance(resolved, dict):
        return resolved
    path = _scoreboard_path(resolved)
    if not path.is_file():
        return {"error": f"scoreboard not found at {path}", "climb_root": str(resolved)}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"error": f"scoreboard JSON invalid: {e}", "path": str(path)}
    if not isinstance(raw, dict):
        return {"error": "scoreboard root must be an object", "path": str(path)}
    out = _board_slice(raw)
    out["scoreboard_path"] = str(path)
    out["climb_root"] = str(resolved)
    return out


def refresh_and_read() -> dict:
    """Optionally run climb `refresh_scoreboard.py`, then read the board.

    Refresh runs only when `FACTORY_CLIMB_REFRESH=1`. Never CreateSubmission.
    Surfaces stderr on failure; does not invent scores.
    """
    resolved = climb_root()
    if isinstance(resolved, dict):
        return resolved
    want = (os.environ.get(REFRESH_ENV) or "").strip() in ("1", "true", "TRUE", "yes", "YES")
    meta: dict[str, Any] = {"refresh_requested": want, "refreshed": False}
    if want:
        script = resolved / REFRESH_SCRIPT_REL
        if not script.is_file():
            return {**meta, "error": f"refresh script missing: {script}", "climb_root": str(resolved)}
        try:
            proc = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(resolved),
                capture_output=True,
                text=True,
                timeout=REFRESH_TIMEOUT_S,
                env=os.environ.copy(),
            )
        except subprocess.TimeoutExpired:
            return {**meta, "error": f"refresh timed out after {REFRESH_TIMEOUT_S}s",
                    "climb_root": str(resolved)}
        meta["refresh_returncode"] = proc.returncode
        meta["refresh_stdout_tail"] = (proc.stdout or "")[-2000:]
        meta["refresh_stderr_tail"] = (proc.stderr or "")[-2000:]
        if proc.returncode != 0:
            return {**meta, "error": "refresh_scoreboard.py failed",
                    "climb_root": str(resolved)}
        meta["refreshed"] = True
    board = read_scoreboard(resolved)
    if "error" in board:
        return {**meta, **board}
    board.update(meta)
    return board


def kaggle_submissions_snapshot() -> dict:
    """COMPLETE/PENDING summary from the climb board (refresh if env set)."""
    board = refresh_and_read()
    if "error" in board and "history_summary" not in board:
        return board
    summary = board.get("history_summary") or {}
    return {
        "ok": "error" not in board,
        "source": "climb_scoreboard",
        "refreshed": bool(board.get("refreshed")),
        "refresh_requested": bool(board.get("refresh_requested")),
        "best_public_score": board.get("best_public_score"),
        "best_public_score_ref": board.get("best_public_score_ref"),
        "pending_submit_utc": board.get("pending_submit_utc"),
        "pending_queue_note": board.get("pending_queue_note"),
        "counts": summary.get("counts", {}),
        "pending": summary.get("pending", []),
        "recent_complete": summary.get("recent_complete", []),
        "latest": summary.get("latest"),
        "scoreboard_path": board.get("scoreboard_path"),
        "error": board.get("error"),
        "refresh_stderr_tail": board.get("refresh_stderr_tail"),
    }


def _scores_disagree(a: Any, b: Any, tol: float = 1e-9) -> bool:
    try:
        if a is None or b is None:
            return a != b and not (a is None and b is None)
        return abs(float(a) - float(b)) > tol
    except (TypeError, ValueError):
        return a != b


def dual_status(factory_status_dict: dict) -> dict:
    """Attach climb slice + sources + score_mismatch to a factory status dict."""
    out = dict(factory_status_dict)
    climb = read_scoreboard()
    factory_best = factory_status_dict.get("best_public_score")
    climb_best = climb.get("best_public_score") if "error" not in climb else None
    mismatch = False
    mismatch_note = None
    if "error" not in climb and _scores_disagree(factory_best, climb_best):
        mismatch = True
        mismatch_note = (
            f"Factory CSV best public_score={factory_best} "
            f"({factory_status_dict.get('best_version')}) ≠ climb/Kaggle "
            f"best_public_score={climb_best} "
            f"(ref={climb.get('best_public_score_ref')}). "
            "Climb/Kaggle is the live publicScore source of truth; the CSV is "
            "factory gate bookkeeping and may disagree."
        )
        warnings = list(out.get("warnings") or [])
        warnings.append(mismatch_note)
        out["warnings"] = warnings
    out["climb"] = climb if "error" in climb else {
        "best_public_score": climb.get("best_public_score"),
        "best_public_score_ref": climb.get("best_public_score_ref"),
        "pending_submit_utc": climb.get("pending_submit_utc"),
        "last_submit_utc": climb.get("last_submit_utc"),
        "tip_git_commit": climb.get("tip_git_commit"),
        "tip_hypothesis": climb.get("tip_hypothesis"),
        "next_tip_plan": climb.get("next_tip_plan"),
        "pending_queue_note": climb.get("pending_queue_note"),
        "history_summary": climb.get("history_summary"),
        "scoreboard_path": climb.get("scoreboard_path"),
        "climb_root": climb.get("climb_root"),
    }
    out["sources"] = {
        "factory_csv": "results/leaderboard.csv",
        "climb_board": str((_scoreboard_path(Path(climb["climb_root"]))
                            if isinstance(climb.get("climb_root"), str)
                            else SCOREBOARD_REL)),
        "kaggle_api": "via climb scripts/refresh_scoreboard.py (optional FACTORY_CLIMB_REFRESH=1)",
    }
    if "error" in climb:
        out["sources"]["climb_board"] = f"unavailable: {climb.get('error')}"
    out["score_mismatch"] = mismatch
    if mismatch_note:
        out["score_mismatch_note"] = mismatch_note
    return out
