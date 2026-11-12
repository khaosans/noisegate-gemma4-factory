"""Sandboxed workspace and the six tools the supervisor exposes.

Each task runs in a fresh copy of the repository (a temporary git checkout), so every
change is reversible and the diff is measured against a known base commit.

Isolation levels (NOISEGATE_SANDBOX, default `auto`):
  seatbelt  macOS default. Each shell/test command runs under `sandbox-exec`: no network, no
            writes outside the task's temporary folder, no reads under /Users or /Volumes
            except the Python installation.
  docker    each shell/test command runs in `docker run --rm --network none` with only the
            workspace mounted.
  local     no OS isolation: subprocess in the copy with a scrubbed environment and timeouts.
            `python -c` and the tests run arbitrary code, so the policy alone does not contain
            a model here. Fine for scripted models; `python -m supervisor` refuses to drive a
            live model in this mode unless --unsafe-no-sandbox is passed.
  auto      seatbelt where `sandbox-exec` exists, otherwise local.
Tools are only ever called after `guardrails.Policy.check` returned ALLOW.
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from guardrails.policy import Policy

OUTPUT_LIMIT = 4000
CMD_TIMEOUT_S = 120
DOCKER_IMAGE = os.environ.get("NOISEGATE_SANDBOX_IMAGE", "python:3.12-slim")
SANDBOX_EXEC = "/usr/bin/sandbox-exec"
SANDBOX_MODES = ("seatbelt", "docker", "local")


def resolve_sandbox(mode: str | None = None) -> str:
    mode = (mode or os.environ.get("NOISEGATE_SANDBOX") or "auto").lower()
    if mode == "auto":
        return "seatbelt" if sys.platform == "darwin" and os.path.exists(SANDBOX_EXEC) else "local"
    if mode not in SANDBOX_MODES:
        raise ValueError(f"NOISEGATE_SANDBOX must be one of auto, {', '.join(SANDBOX_MODES)}; got {mode!r}")
    return mode


def _sb_quote(path: str) -> str:
    return '"' + path.replace("\\", "\\\\").replace('"', '\\"') + '"'


def seatbelt_profile(writable: str) -> str:
    """Deny network, writes outside `writable`, and reads of user data. Later rules win."""
    readable = {os.path.realpath(p) for p in (writable, sys.prefix, sys.base_prefix)}
    return "\n".join([
        "(version 1)",
        "(allow default)",
        "(deny network*)",
        "(deny file-write*)",
        f'(allow file-write* (subpath {_sb_quote(writable)}) (literal "/dev/null") (literal "/dev/tty")'
        ' (literal "/dev/dtracehelper") (regex #"/xcrun_db[^/]*$"))',
        '(deny file-read* (subpath "/Users") (subpath "/Volumes"))',
        '(allow file-read-metadata (subpath "/Users"))',
        "(allow file-read* " + " ".join(f"(subpath {_sb_quote(p)})" for p in sorted(readable)) + ")",
    ])


@dataclass
class ToolResult:
    ok: bool
    output: str
    edit_attempt: bool = False  # counts toward the failed-edit breaker


def _clip(text: str, limit: int = OUTPUT_LIMIT) -> str:
    text = text or ""
    return text if len(text) <= limit else text[: limit // 2] + "\n...[truncated]...\n" + text[-limit // 2:]


def _git(ws: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(ws), *args], capture_output=True, text=True,
                          check=True).stdout


class Workspace:
    def __init__(self, source: str | Path, root: str | Path | None = None):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="noisegate-ws-", dir=root))
        (Path(self.tmp) / "tmp").mkdir()
        self.path = Path(self.tmp) / "repo"
        shutil.copytree(source, self.path, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".pytest_cache", ".venv", "node_modules"))
        _git(self.path, "init", "-q")
        _git(self.path, "-c", "user.email=sandbox@noisegate", "-c", "user.name=sandbox",
             "add", "-A")
        _git(self.path, "-c", "user.email=sandbox@noisegate", "-c", "user.name=sandbox",
             "commit", "-q", "-m", "base", "--allow-empty")
        (self.path / ".git" / "info" / "exclude").write_text(
            "__pycache__/\n*.pyc\n.pytest_cache/\n", encoding="utf-8")
        self.policy = Policy(self.path)
        self.sandbox = resolve_sandbox()

    @property
    def isolated(self) -> bool:
        """True when the OS, not only the policy, confines shell and test commands."""
        return self.sandbox in ("seatbelt", "docker")

    def cleanup(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- process execution ----
    def _env(self) -> dict[str, str]:
        path = os.pathsep.join([str(Path(sys.executable).parent), os.environ.get("PATH", "/usr/bin:/bin")])
        return {"PATH": path, "HOME": str(self.path), "TMPDIR": str(Path(self.tmp) / "tmp"),
                "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(self.path),
                "NO_COLOR": "1"}

    def run(self, cmd: str, timeout: int = CMD_TIMEOUT_S) -> tuple[int, str]:
        if self.sandbox == "docker":
            argv = ["docker", "run", "--rm", "--network", "none", "-v", f"{self.path}:/workspace",
                    "-w", "/workspace", "-e", "PYTHONPATH=/workspace", DOCKER_IMAGE, "sh", "-c", cmd]
            kwargs = {}
        elif self.sandbox == "seatbelt":
            argv = [SANDBOX_EXEC, "-p", seatbelt_profile(self.tmp), "/bin/sh", "-c", cmd]
            kwargs = {"cwd": self.path, "env": self._env()}
        else:
            argv, kwargs = cmd, {"shell": True, "cwd": self.path, "env": self._env()}
        try:
            p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, **kwargs)
            return p.returncode, _clip((p.stdout or "") + (p.stderr or ""))
        except subprocess.TimeoutExpired:
            return 124, f"command timed out after {timeout} s"

    # ---- diff ----
    def diff(self) -> tuple[list[str], int, str]:
        """(changed paths, lines added + removed, unified diff) against the base commit."""
        _git(self.path, "add", "-A")
        names = [n for n in _git(self.path, "diff", "--cached", "--name-only").splitlines() if n]
        numstat = _git(self.path, "diff", "--cached", "--numstat")
        lines = 0
        for row in numstat.splitlines():
            a, d, *_ = row.split("\t")
            lines += (int(a) if a.isdigit() else 0) + (int(d) if d.isdigit() else 0)
        patch = _git(self.path, "diff", "--cached")
        _git(self.path, "reset", "-q")
        return names, lines, patch

    # ---- tools (called only after Policy.check returned ALLOW) ----
    def read(self, path: str, start: int = 1, end: int | None = None) -> ToolResult:
        f = self.path / self.policy.rel(path)
        if not f.is_file():
            return ToolResult(False, f"not a file: {path}")
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        end = min(end or start + 199, len(lines))
        body = "\n".join(f"{i:>5}  {lines[i - 1]}" for i in range(start, end + 1))
        return ToolResult(True, _clip(f"{path} lines {start}-{end} of {len(lines)}\n{body}"))

    def search(self, pattern: str, path: str = ".") -> ToolResult:
        rel = self.policy.rel(path)
        code, out = self.run(f"git grep -n -I -F -e {shlex.quote(pattern)} -- {shlex.quote(rel)} | head -n 60")
        return ToolResult(True, out or "no matches")

    def edit(self, path: str, old: str, new: str) -> ToolResult:
        f = self.path / self.policy.rel(path)
        if not f.is_file():
            return ToolResult(False, f"edit failed: not a file: {path}", edit_attempt=True)
        text = f.read_text(encoding="utf-8")
        n = text.count(old)
        if n != 1:
            hint = "not found" if n == 0 else f"occurs {n} times; include more context"
            return ToolResult(False, f"edit failed: old text {hint}. Re-read the file and copy it exactly.",
                              edit_attempt=True)
        f.write_text(text.replace(old, new, 1), encoding="utf-8")
        return ToolResult(True, f"edited {path}", edit_attempt=True)

    def write(self, path: str, content: str) -> ToolResult:
        f = self.path / self.policy.rel(path)
        if f.exists():
            return ToolResult(False, f"write failed: {path} exists; use edit", edit_attempt=True)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        return ToolResult(True, f"created {path}", edit_attempt=True)

    def shell(self, cmd: str) -> ToolResult:
        code, out = self.run(cmd)
        return ToolResult(code == 0, f"exit {code}\n{out}")

    def test(self, target: str | None = None, default_cmd: str = "python -m pytest -q -x") -> ToolResult:
        cmd = default_cmd if not target else f"python -m pytest -q -x {shlex.quote(target)}"
        code, out = self.run(cmd)
        return ToolResult(code == 0, f"exit {code}\n{out}")


_PASSED = re.compile(r"(\d+) passed")


def tests_passed(output: str) -> bool:
    return output.startswith("exit 0") and bool(_PASSED.search(output))
