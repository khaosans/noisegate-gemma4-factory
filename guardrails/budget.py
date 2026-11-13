"""Hard budgets: tool calls, wall-clock time, and a failed-edit circuit breaker.

Defaults match the competition: 28 tool calls and 8 minutes per task. The breaker
trips after 3 consecutive failed edits (gate v5 had runs with 59-70 failed edits).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Budget:
    max_calls: int = 28
    max_seconds: float = 480.0
    breaker_failed_edits: int = 3
    max_breaker_trips: int = 2  # second trip escalates instead of falling back


@dataclass
class BudgetTracker:
    budget: Budget = field(default_factory=Budget)
    clock: Callable[[], float] = time.monotonic
    calls: int = 0
    failed_edit_streak: int = 0
    breaker_trips: int = 0
    started: float | None = None

    def start(self) -> None:
        self.started = self.clock()

    @property
    def elapsed(self) -> float:
        return 0.0 if self.started is None else self.clock() - self.started

    @property
    def calls_left(self) -> int:
        return max(0, self.budget.max_calls - self.calls)

    @property
    def seconds_left(self) -> float:
        return max(0.0, self.budget.max_seconds - self.elapsed)

    def exhausted(self) -> bool:
        return self.calls >= self.budget.max_calls or self.elapsed >= self.budget.max_seconds

    def spend_call(self) -> None:
        self.calls += 1

    def record_edit(self, ok: bool) -> str | None:
        """Returns None, "fallback" (first trip) or "escalate" (trip limit reached)."""
        if ok:
            self.failed_edit_streak = 0
            return None
        self.failed_edit_streak += 1
        if self.failed_edit_streak < self.budget.breaker_failed_edits:
            return None
        self.failed_edit_streak = 0
        self.breaker_trips += 1
        return "escalate" if self.breaker_trips >= self.budget.max_breaker_trips else "fallback"

    def banner(self) -> str:
        """Budget made visible to the model inside tool results (decision 006)."""
        return f"[call {self.calls} of {self.budget.max_calls} | {int(self.seconds_left)} s left]"
