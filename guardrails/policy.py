"""Tool access policy: allow-list, schema-validated arguments, workspace paths, shell rules.

Every tool call the model proposes passes through `Policy.check` before it runs.
The verdict is one of:

- ALLOW     run it.
- BLOCK     do not run it; return the reason to the model so it can choose a safe fallback.
- ESCALATE  do not run it; stop and hand the run to a human (boundary-crossing actions).

Reason codes are stable strings so traces, metrics and tests can count them.
"""
from __future__ import annotations

import re
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Action(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"


class Verdict(BaseModel):
    action: Action
    reason: str = "OK"  # stable code, e.g. TEST_FILE_EDIT
    detail: str = ""

    @property
    def runs(self) -> bool:
        return self.action is Action.ALLOW


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


# ---- argument schemas (the allow-list) -------------------------------------------------

class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReadArgs(_Args):
    path: str
    start: int = Field(1, ge=1)
    end: Optional[int] = Field(None, ge=1)


class SearchArgs(_Args):
    pattern: str = Field(min_length=1, max_length=200)
    path: str = "."


class EditArgs(_Args):
    path: str
    old: str = Field(min_length=1)
    new: str


class WriteArgs(_Args):
    path: str
    content: str


class ShellArgs(_Args):
    cmd: str = Field(min_length=1, max_length=2000)


class TestArgs(_Args):
    target: Optional[str] = None


class SubmitArgs(_Args):
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = ""


class EscalateArgs(_Args):
    reason: str = Field(min_length=3, max_length=500)


TOOL_SCHEMAS: dict[str, type[_Args]] = {
    "read": ReadArgs,
    "search": SearchArgs,
    "edit": EditArgs,
    "write": WriteArgs,
    "shell": ShellArgs,
    "test": TestArgs,
    "submit": SubmitArgs,
    "escalate": EscalateArgs,
}

# ---- path rules ------------------------------------------------------------------------

TEST_PATH = re.compile(
    r"(^|/)(tests?|testing)/|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$|(^|/)pytest\.ini$|(^|/)tox\.ini$"
)
SENSITIVE_PATH = re.compile(
    r"(^|/)\.github/|(^|/)\.gitlab-ci|(^|/)\.circleci/|(^|/)Jenkinsfile$|(^|/)\.env|auth|secret|credential"
    r"|(^|/)(setup\.cfg|pyproject\.toml|setup\.py|Dockerfile|Makefile)$",
    re.IGNORECASE,
)


SECRET_FILE = re.compile(
    r"(^|/)(\.env(\.[^/]*)?|kaggle\.json|\.netrc|\.pypirc|id_rsa|id_ed25519|[^/]*\.pem|[^/]*\.key)$"
)


def is_secret_path(rel: str) -> bool:
    return bool(SECRET_FILE.search(rel.replace("\\", "/")))


def is_test_path(rel: str) -> bool:
    return bool(TEST_PATH.search(rel.replace("\\", "/")))


def is_sensitive_path(rel: str) -> bool:
    return bool(SENSITIVE_PATH.search(rel.replace("\\", "/")))


class Policy:
    """Deny by default: only the tools in TOOL_SCHEMAS, only inside the workspace."""

    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace).resolve()

    # -- helpers --
    def rel(self, path: str) -> Optional[str]:
        """Workspace-relative POSIX path, or None if it escapes the workspace."""
        if not path or "\x00" in path:
            return None
        p = Path(path).expanduser()
        target = (p if p.is_absolute() else self.workspace / p).resolve()
        try:
            rel = target.relative_to(self.workspace)
        except ValueError:
            return None
        rel_s = PurePosixPath(*rel.parts).as_posix() if rel.parts else "."
        if rel_s == ".git" or rel_s.startswith(".git/"):
            return None
        return rel_s

    def _path_verdict(self, path: str, writing: bool) -> Optional[Verdict]:
        rel = self.rel(path)
        if rel is None:
            return Verdict(action=Action.BLOCK, reason="PATH_OUTSIDE_WORKSPACE", detail=path)
        if is_secret_path(rel):
            return Verdict(action=Action.BLOCK, reason="SECRET_ACCESS", detail=rel)
        if writing and is_test_path(rel):
            return Verdict(action=Action.BLOCK, reason="TEST_FILE_EDIT", detail=rel)
        return None

    # -- entry point --
    def check(self, call: ToolCall) -> Verdict:
        schema = TOOL_SCHEMAS.get(call.name)
        if schema is None:
            return Verdict(action=Action.BLOCK, reason="TOOL_NOT_ALLOWED", detail=call.name)
        try:
            args = schema.model_validate(call.args)
        except ValidationError as e:
            first = e.errors()[0]
            return Verdict(action=Action.BLOCK, reason="BAD_ARGS",
                           detail=f"{'.'.join(map(str, first['loc']))}: {first['msg']}")

        if isinstance(args, (ReadArgs, SearchArgs)):
            v = self._path_verdict(args.path, writing=False)
        elif isinstance(args, (EditArgs, WriteArgs)):
            v = self._path_verdict(args.path, writing=True)
        elif isinstance(args, TestArgs) and args.target:
            v = self._path_verdict(args.target.split("::")[0], writing=False)
        elif isinstance(args, ShellArgs):
            v = self._shell_verdict(args.cmd)
        else:
            v = None
        return v or Verdict(action=Action.ALLOW)

    def _shell_verdict(self, cmd: str) -> Optional[Verdict]:
        from .shell import shell_verdict  # allow-list rules live in guardrails/shell.py
        return shell_verdict(self, cmd)
