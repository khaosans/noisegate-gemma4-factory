"""Input checks: repository and issue text are data, never instructions."""
from __future__ import annotations

import re

_MARKERS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"disregard (the |your )?(system|previous) (prompt|instructions)",
    r"you are now",
    r"(edit|modify|update|change|delete) (the )?(tests?|test files?|conftest)",
    r"\b(pip3?|npm|apt(-get)?) install\b",
    r"\b(curl|wget)\s+https?://",
    r"\bgit push\b",
    r"\b(printenv|os\.environ|\$\{?[A-Z_]*(KEY|TOKEN|SECRET)[A-Z_]*\}?)",
    r"rm\s+-rf\s+(/|~)",
]
_MARKER_RE = re.compile("|".join(f"(?:{m})" for m in _MARKERS), re.IGNORECASE)


def scan_injection(text: str) -> list[str]:
    """Phrases that look like instructions aimed at the agent. Flags, never blocks."""
    return sorted({m.group(0).lower() for m in _MARKER_RE.finditer(text or "")})


def wrap_untrusted(label: str, text: str) -> str:
    """Delimit untrusted text so the prompt can refer to it as data."""
    safe = (text or "").replace("</untrusted>", "&lt;/untrusted&gt;")
    return f'<untrusted source="{label}">\n{safe}\n</untrusted>'
