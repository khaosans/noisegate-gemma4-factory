"""Output constraints on a submitted patch (Checkpoint 6.1, sections 2 and 4).

Hard failures (the patch is rejected and the model is told why):
  EMPTY_DIFF          no source file changed
  TEST_FILE_CHANGED   a test file or test config changed
  SYNTAX_ERROR        a changed .py file does not parse

Review flags (the patch may be fine, but a human looks before it is accepted):
  LARGE_DIFF          more than `max_lines` lines added + removed
  SENSITIVE_FILE      CI, auth, packaging or environment files touched
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from .policy import is_sensitive_path, is_test_path

MAX_DIFF_LINES = 100


@dataclass
class PatchReport:
    changed: list[str]
    lines_changed: int
    failures: list[str] = field(default_factory=list)
    review_flags: list[str] = field(default_factory=list)
    detail: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def source_files(self) -> list[str]:
        return [p for p in self.changed if not is_test_path(p)]


def check_patch(workspace: str | Path, changed: list[str], lines_changed: int,
                max_lines: int = MAX_DIFF_LINES) -> PatchReport:
    ws = Path(workspace)
    r = PatchReport(changed=sorted(changed), lines_changed=lines_changed)
    tests = [p for p in r.changed if is_test_path(p)]
    if tests:
        r.failures.append("TEST_FILE_CHANGED")
        r.detail.append("test files changed: " + ", ".join(tests))
    if not r.source_files:
        r.failures.append("EMPTY_DIFF")
        r.detail.append("no source file changed")
    for p in r.source_files:
        f = ws / p
        if p.endswith(".py") and f.exists():
            try:
                ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=p)
            except SyntaxError as e:
                r.failures.append("SYNTAX_ERROR")
                r.detail.append(f"{p}:{e.lineno}: {e.msg}")
    if lines_changed > max_lines:
        r.review_flags.append("LARGE_DIFF")
        r.detail.append(f"{lines_changed} lines changed (limit {max_lines})")
    sensitive = [p for p in r.changed if is_sensitive_path(p)]
    if sensitive:
        r.review_flags.append("SENSITIVE_FILE")
        r.detail.append("sensitive files: " + ", ".join(sensitive))
    return r
