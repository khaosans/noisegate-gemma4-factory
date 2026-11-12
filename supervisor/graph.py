"""LangGraph supervisor: Gemma proposes one tool call per step; code decides what runs.

    START -> intake -> agent -> guard -> execute -> agent ...      (one tool call per loop)
                         |        |         |
                         |        |         +-> verify -> finalize  (submit: patch checks + tests)
                         |        +-> escalate -> finalize          (boundary action, repeated block)
                         +-> escalate (budget gone, edit loop, agent asked for help)

The model never runs a tool directly. `guard` applies guardrails.Policy, `execute` runs the
tool in the sandboxed Workspace, `verify` applies the output constraints and the task's tests,
and `escalate` stops for a human (LangGraph interrupt when hitl=True). Budgets (28 calls,
8 min, failed-edit breaker) are counted in code and shown to the model in every tool result.

Every step is written to the JSONL run log (agentops.tracelog) and, when LANGSMITH_TRACING=true,
traced to LangSmith with the run id, task id and config as metadata.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Optional, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

from agentops.tracelog import RunLog
from guardrails.budget import Budget, BudgetTracker
from guardrails.output import check_patch
from guardrails.policy import Action, ToolCall, is_test_path
from guardrails.untrusted import scan_injection, wrap_untrusted

from .prompts import SYSTEM_PROMPT, task_message
from .protocol import parse_action
from .tools import ToolResult, Workspace, tests_passed

MAX_TEST_RETRIES = 1  # failing tests after submit: send back once, then escalate


class Task(BaseModel):
    task_id: str
    repo: str                      # path to the repository to copy into the sandbox
    issue: str                     # untrusted
    test_cmd: str = "python -m pytest -q"
    gold_files: list[str] = Field(default_factory=list)  # optional, for groundedness


class State(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    route: str
    pending: Optional[dict]
    status: str
    escalation: Optional[dict]
    human_decision: Optional[dict]
    submitted: Optional[dict]
    verify: Optional[dict]


@dataclass
class Runtime:
    """Per-run objects that are not graph state (not serialized by the checkpointer)."""
    task: Task
    ws: Workspace
    budget: BudgetTracker
    log: RunLog
    model_name: str
    hitl: bool
    counters: dict = field(default_factory=lambda: {
        "model_calls": 0, "tokens_in": 0, "tokens_out": 0, "malformed": 0, "blocked": 0,
        "blocked_reasons": {}, "failed_edits": 0, "recovered_after_failed_edit": None,
        "first_edit_call": None, "test_retries": 0, "submit_rejections": 0})
    block_sigs: dict = field(default_factory=dict)
    injection_flags: list = field(default_factory=list)
    escalation_logged: bool = False


def _sig(call: ToolCall) -> str:
    return call.name + ":" + json.dumps(call.args, sort_keys=True)


def build_graph(model: BaseChatModel, rt: Runtime, checkpointer=None):
    c = rt.counters

    def tool_msg(text: str) -> HumanMessage:
        return HumanMessage(content=f"{rt.budget.banner()}\n{text}")

    def intake(state: State) -> dict:
        rt.budget.start()
        rt.injection_flags = scan_injection(rt.task.issue)
        rt.log.event("run_start", model=rt.model_name, issue_chars=len(rt.task.issue),
                     injection_flags=rt.injection_flags, budget=rt.budget.budget.__dict__)
        issue = wrap_untrusted("issue", rt.task.issue)
        return {"messages": [SystemMessage(content=SYSTEM_PROMPT),
                             HumanMessage(content=task_message(issue, rt.injection_flags))],
                "status": "RUNNING", "route": "agent"}

    def agent(state: State) -> dict:
        if rt.budget.exhausted():
            return {"route": "escalate", "escalation": {
                "reason": "BUDGET_EXHAUSTED", "detail": f"{rt.budget.calls} calls, {int(rt.budget.elapsed)} s, no accepted patch"}}
        t0 = time.monotonic()
        reply = model.invoke(state["messages"])
        usage = getattr(reply, "usage_metadata", None) or {}
        c["model_calls"] += 1
        c["tokens_in"] += int(usage.get("input_tokens", 0) or 0)
        c["tokens_out"] += int(usage.get("output_tokens", 0) or 0)
        call, err = parse_action(reply)
        rt.log.event("model_call", ms=int((time.monotonic() - t0) * 1000), usage=usage,
                     parsed=call.model_dump() if call else None, error=err or None)
        ai = reply if isinstance(reply, AIMessage) else AIMessage(content=str(reply))
        if call is None:
            rt.budget.spend_call()
            c["malformed"] += 1
            return {"messages": [ai, tool_msg(f"ERROR malformed reply: {err}")], "route": "agent"}
        return {"messages": [ai], "pending": call.model_dump(), "route": "guard"}

    def guard(state: State) -> dict:
        call = ToolCall(**state["pending"])
        rt.budget.spend_call()
        v = rt.ws.policy.check(call)
        rt.log.event("tool_call", call_no=rt.budget.calls, tool=call.name, args=call.args,
                     verdict=v.action.value, reason=v.reason, detail=v.detail)
        if v.action is Action.ALLOW:
            return {"route": "execute"}
        if v.action is Action.ESCALATE:
            return {"route": "escalate", "escalation": {"reason": v.reason, "detail": v.detail,
                                                       "call": call.model_dump()}}
        c["blocked"] += 1
        c["blocked_reasons"][v.reason] = c["blocked_reasons"].get(v.reason, 0) + 1
        sig = _sig(call)
        rt.block_sigs[sig] = rt.block_sigs.get(sig, 0) + 1
        if rt.block_sigs[sig] >= 2:
            return {"route": "escalate", "escalation": {
                "reason": "REPEATED_BLOCK", "detail": f"{v.reason} twice: {v.detail}", "call": call.model_dump()}}
        return {"messages": [tool_msg(f"BLOCKED {v.reason}: {v.detail}. This action is not allowed; choose a different, safe action.")],
                "route": "agent"}

    def execute(state: State) -> dict:
        call = ToolCall(**state["pending"])
        a = call.args
        if call.name == "submit":
            return {"route": "verify", "submitted": dict(a)}
        if call.name == "escalate":
            return {"route": "escalate", "escalation": {"reason": "AGENT_REQUESTED", "detail": a["reason"]}}
        t0 = time.monotonic()
        ws = rt.ws
        res: ToolResult = {
            "read": lambda: ws.read(a["path"], a.get("start", 1), a.get("end")),
            "search": lambda: ws.search(a["pattern"], a.get("path", ".")),
            "edit": lambda: ws.edit(a["path"], a["old"], a["new"]),
            "write": lambda: ws.write(a["path"], a["content"]),
            "shell": lambda: ws.shell(a["cmd"]),
            "test": lambda: ws.test(a.get("target"), rt.task.test_cmd),
        }[call.name]()
        extra: list[str] = []
        if res.edit_attempt:
            if res.ok and c["first_edit_call"] is None:
                c["first_edit_call"] = rt.budget.calls
            if not res.ok:
                c["failed_edits"] += 1
                if c["recovered_after_failed_edit"] is None:
                    c["recovered_after_failed_edit"] = False
            elif c["recovered_after_failed_edit"] is False:
                c["recovered_after_failed_edit"] = True
            trip = rt.budget.record_edit(res.ok)
            if trip == "fallback":
                extra.append("CIRCUIT BREAKER: 3 edits failed in a row. Stop editing that region. "
                             "Re-read the file around the change, then make one smaller edit.")
                rt.log.event("breaker", action="fallback")
            elif trip == "escalate":
                rt.log.event("breaker", action="escalate")
                return {"route": "escalate", "escalation": {
                    "reason": "EDIT_LOOP", "detail": f"circuit breaker tripped {rt.budget.breaker_trips} times"}}
        rt.log.event("tool_result", call_no=rt.budget.calls, tool=call.name, ok=res.ok,
                     ms=int((time.monotonic() - t0) * 1000), output=res.output[:500])
        text = f"{call.name} -> {res.output}" + ("\n" + "\n".join(extra) if extra else "")
        return {"messages": [tool_msg(text)], "route": "agent"}

    def verify(state: State) -> dict:
        names, lines, _ = rt.ws.diff()
        rep = check_patch(rt.ws.path, names, lines)
        ok_tests, out = None, ""
        if rep.ok:
            res = rt.ws.test(None, rt.task.test_cmd)
            ok_tests, out = tests_passed(res.output), res.output
        info = {"changed": rep.changed, "lines": lines, "failures": rep.failures,
                "review_flags": rep.review_flags, "detail": rep.detail, "tests_passed": ok_tests,
                "confidence": (state.get("submitted") or {}).get("confidence")}
        rt.log.event("verify", **info, test_tail=out[-600:])
        if not rep.ok:
            c["submit_rejections"] += 1
            if rt.budget.exhausted():
                return {"verify": info, "route": "escalate", "escalation": {
                    "reason": "BUDGET_EXHAUSTED", "detail": "last submit rejected: " + "; ".join(rep.detail)}}
            return {"verify": info, "route": "agent", "messages": [tool_msg(
                "SUBMIT REJECTED: " + "; ".join(rep.detail) + ". Fix this, then submit again.")]}
        if not ok_tests:
            if c["test_retries"] < MAX_TEST_RETRIES and not rt.budget.exhausted():
                c["test_retries"] += 1
                return {"verify": info, "route": "agent", "messages": [tool_msg(
                    "SUBMIT REJECTED: tests still fail after your patch:\n" + out[-1500:])]}
            return {"verify": info, "route": "escalate", "escalation": {
                "reason": "TESTS_FAIL_AFTER_PATCH", "detail": out[-300:]}}
        if rep.review_flags:
            return {"verify": info, "route": "escalate", "escalation": {
                "reason": "HIGH_IMPACT_DIFF", "detail": "; ".join(rep.detail), "tests_passed": True}}
        return {"verify": info, "route": "finalize", "status": "RESOLVED"}

    def escalate(state: State) -> dict:
        esc = state.get("escalation") or {"reason": "UNKNOWN"}
        if not rt.escalation_logged:  # a resumed interrupt re-runs this node
            rt.log.event("escalate", **esc)
            rt.escalation_logged = True
        decision = None
        if rt.hitl:
            decision = interrupt({"run_id": rt.log.run_id, "task_id": rt.task.task_id, **esc})
            if isinstance(decision, str):
                decision = {"decision": decision}
            rt.log.event("human_decision", **(decision or {}))
        status = "ESCALATED"
        if (decision or {}).get("decision") == "approve" and esc.get("reason") == "HIGH_IMPACT_DIFF" \
                and esc.get("tests_passed"):
            status = "RESOLVED"
        return {"status": status, "human_decision": decision, "route": "finalize"}

    def finalize(state: State) -> dict:
        names, lines, _ = rt.ws.diff()
        v = state.get("verify") or {}
        esc = state.get("escalation") or {}
        status = state.get("status") or "FAILED"
        if status == "RUNNING":
            status = "FAILED"
        gold = rt.task.gold_files
        rt.log.event("run_end", status=status)
        rt.log.summary(
            model=rt.model_name, status=status, resolved=status == "RESOLVED",
            escalation_reason=esc.get("reason") if status == "ESCALATED" else None,
            human_decision=(state.get("human_decision") or {}).get("decision"),
            tests_passed=v.get("tests_passed"), confidence=v.get("confidence"),
            calls=rt.budget.calls, seconds=round(rt.budget.elapsed, 1),
            over_budget=rt.budget.exhausted(),
            changed_files=names, lines_changed=lines,
            empty_diff=not [n for n in names if not is_test_path(n)],
            gold_hit=(bool(set(gold) & set(names)) if gold else None),
            injection_flags=rt.injection_flags, breaker_trips=rt.budget.breaker_trips,
            **{k: v2 for k, v2 in c.items()})
        return {"status": status}

    def route(state: State) -> str:
        return state["route"]

    g = StateGraph(State)
    for name, fn in [("intake", intake), ("agent", agent), ("guard", guard), ("execute", execute),
                     ("verify", verify), ("escalate", escalate), ("finalize", finalize)]:
        g.add_node(name, fn)
    g.add_edge(START, "intake")
    g.add_edge("intake", "agent")
    g.add_conditional_edges("agent", route, ["agent", "guard", "escalate"])
    g.add_conditional_edges("guard", route, ["execute", "agent", "escalate"])
    g.add_conditional_edges("execute", route, ["agent", "verify", "escalate"])
    g.add_conditional_edges("verify", route, ["agent", "escalate", "finalize"])
    g.add_edge("escalate", "finalize")
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)


class Supervisor:
    """Runs one task end to end. With hitl=True, `run()` may pause for a human; call `resume()`."""

    def __init__(self, model: BaseChatModel, task: Task, *, budget: Budget | None = None,
                 runs_dir: str | Path | None = None, config_name: str = "supervisor-v1",
                 model_name: str | None = None, hitl: bool = False, clock=None):
        tracker = BudgetTracker(budget or Budget())
        if clock is not None:
            tracker.clock = clock
        self.rt = Runtime(task=task, ws=Workspace(task.repo), budget=tracker,
                          log=RunLog(task.task_id, config_name, root=runs_dir),
                          model_name=model_name or type(model).__name__, hitl=hitl)
        self.app = build_graph(model, self.rt, checkpointer=InMemorySaver() if hitl else None)
        self.config = {
            "run_name": f"noisegate {task.task_id}",
            "tags": ["noisegate", config_name],
            "metadata": {"run_id": self.rt.log.run_id, "task_id": task.task_id, "config": config_name},
            "configurable": {"thread_id": self.rt.log.run_id},
            "recursion_limit": 10 * (budget or Budget()).max_calls + 50,
        }

    @property
    def run_id(self) -> str:
        return self.rt.log.run_id

    def _result(self, out: dict) -> dict:
        if "__interrupt__" in out:
            return {"status": "AWAITING_HUMAN", "run_id": self.run_id,
                    "escalation": out["__interrupt__"][0].value}
        return {"status": out.get("status"), "run_id": self.run_id,
                "escalation": out.get("escalation"), "verify": out.get("verify")}

    def run(self) -> dict:
        return self._result(self.app.invoke({}, self.config))

    def resume(self, decision: str, note: str = "") -> dict:
        return self._result(self.app.invoke(Command(resume={"decision": decision, "note": note}), self.config))

    def diff(self) -> str:
        return self.rt.ws.diff()[2]

    def close(self) -> None:
        self.rt.ws.cleanup()


def run_task(model: BaseChatModel, task: Task, **kwargs: Any) -> dict:
    sup = Supervisor(model, task, **kwargs)
    try:
        return sup.run()
    finally:
        sup.close()
