"""AgentOps: structured run logs, metrics, and a query CLI for the supervisor."""
from .tracelog import RunLog, redact

__all__ = ["RunLog", "redact"]
