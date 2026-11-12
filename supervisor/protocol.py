"""Parse the model's reply into a ToolCall (JSON protocol, or native tool_calls if present)."""
from __future__ import annotations

import json
from typing import Any, Optional

from guardrails.policy import ToolCall

_DECODER = json.JSONDecoder()


def parse_action(message: Any) -> tuple[Optional[ToolCall], str]:
    """Returns (tool_call, error). Exactly one of them is set."""
    native = getattr(message, "tool_calls", None) or []
    if native:
        tc = native[0]
        return ToolCall(name=tc["name"], args=dict(tc.get("args") or {})), ""
    text = message.content if hasattr(message, "content") else str(message)
    if isinstance(text, list):  # content blocks
        text = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in text)
    text = text or ""
    i = text.find("{")
    while i != -1:
        try:
            obj, _ = _DECODER.raw_decode(text, i)
        except json.JSONDecodeError:
            i = text.find("{", i + 1)
            continue
        if isinstance(obj, dict) and isinstance(obj.get("tool"), str):
            args = obj.get("args") or {}
            if not isinstance(args, dict):
                return None, "args must be a JSON object"
            return ToolCall(name=obj["tool"], args=args), ""
        i = text.find("{", i + 1)
    return None, 'reply was not a JSON object like {"tool": "read", "args": {"path": "..."}}'
