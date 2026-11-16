"""The operator chatbot: Claude with the factory's actions as tools, plus an offline fallback.

`ClaudeOperator` runs a tool loop over `factory_console.actions`. `OfflineOperator` maps keywords
to the same actions with no model, so the console still answers without credentials or network.
Both return a `Reply` with the text, every action that ran (for the UI to show), and any write
that is waiting for a human to approve.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from . import actions

MODEL = os.environ.get("FACTORY_CONSOLE_MODEL", "claude-opus-5-5")
MAX_TURNS = 12
RESULT_LIMIT = 30_000  # characters of one tool result sent back to the model

SYSTEM = """You are the operator console for a software factory.

The factory is a loop that builds a coding agent and decides whether each new version ships. The \
product is a Gemma 4 coding agent that fixes GitHub issues within 28 tool calls and about 8 minutes, \
scored by a Kaggle benchmark. Each candidate is the current base config plus exactly one change. The \
Eval Gate runs it on a fixed 30-task set, and a decision rule written in code returns SUBMIT or HOLD.

Measured noise is large: the same config moves by up to 3 in-budget solves per 30 between gate runs, \
and by about 0.05 on the leaderboard. Treat any single-run difference inside that range as a tie and \
say so.

How to work:
- Answer from the tools. They read the repository's records, which are the source of truth. Do not \
answer factory questions from memory, and do not do the decision rule's arithmetic yourself: call \
explain_candidate, decision_rule_what_if or judge_gate_log.
- You can run local jobs (tests, safety eval, zip build, one supervised agent run). Say what you ran \
and what it returned, including failures.
- You cannot start a Kaggle gate run, submit to the leaderboard, or change the base config. Those are \
human decisions in the runbook. If asked, say who does it and what the factory needs first.
- record_score does not write anything. It queues the entry for the human to approve in the console. \
Tell them it is waiting for their approval.
- run_scripted_agent uses a scripted stand-in model, not Gemma. Never describe its result as evidence \
about Gemma. judge_gate_log with no log text uses a synthetic sample; say so when you use it.
- If the records are stale or something is missing, say that plainly.

Write for someone watching a demo: lead with the answer in a sentence or two, then the numbers that \
support it. Use a small table when comparing runs. Keep replies short."""


def _tool(name: str, description: str, properties: dict | None = None, required: list[str] | None = None) -> dict:
    return {"name": name, "description": description,
            "input_schema": {"type": "object", "properties": properties or {},
                             "required": required or [], "additionalProperties": False}}


_S, _I, _N, _B = {"type": "string"}, {"type": "integer"}, {"type": "number"}, {"type": "boolean"}

TOOLS = [
    _tool("factory_status", "Current state of the factory: base, best score, days to the deadline, what the "
          "runbook says is due today, the next queue items, and warnings about stale or missing records. "
          "Call this first for any 'where are we' question."),
    _tool("list_gate_runs", "Every Eval Gate result row (per candidate per run, counts per 30 tasks) with "
          "the recorded verdict."),
    _tool("list_leaderboard", "Every scored public-leaderboard submission."),
    _tool("list_candidates", "All candidate versions with their one change, plus the ordered queue of "
          "changes not yet tried."),
    _tool("explain_candidate", "Why a candidate was held or passed: its gate numbers, its baseline's "
          "numbers, the decision rule replayed on them, and the factory's log notes about it.",
          {"version": {**_S, "description": "e.g. V17"}}, ["version"]),
    _tool("search_log", "Search the dated factory log (results/eval-results.md). Returns newest entries "
          "containing all the words.", {"query": _S, "limit": _I}, ["query"]),
    _tool("read_decisions", "Decision records. Omit number for the list; give a number for the full text.",
          {"number": _I}),
    _tool("read_lessons", "The team's written lessons from the project."),
    _tool("read_goals", "Objectives and key results with their current status."),
    _tool("noise_evidence", "How far the same config moved between runs, locally and on the leaderboard."),
    _tool("decision_rule_what_if", "Run the SUBMIT/HOLD rule on hypothetical numbers against V8's recorded "
          "history. in_budget_runs is the candidate's in-budget solves per 30 for each gate run.",
          {"in_budget_runs": {"type": "array", "items": _I}, "paired_net_run_b": _I,
           "empty_per_run": _N, "overruns_per_run": _N, "test_file_edits": _B, "harness_error": _B,
           "never_scored": _B, "single_run_screen": _B}, ["in_budget_runs"]),
    _tool("judge_gate_log", "Parse Eval Gate log text and apply the decision rule. Omit log_text to use the "
          "bundled synthetic sample.", {"log_text": _S, "candidate": _S, "baseline": _S}),
    _tool("run_tests", "Run the repository's test suite locally. Takes up to a minute."),
    _tool("run_safety_eval", "Run the adversarial prompt-injection cases through the supervisor with a "
          "scripted model. Takes one to two minutes."),
    _tool("build_submission", "Rebuild submission.zip in a temp folder and return SHA-256 hashes. Does not "
          "submit anything."),
    _tool("run_scripted_agent", "Run one supervised agent session on the tinycalc fixture with a scripted "
          "stand-in model. Shows the guardrails and the run log working; says nothing about Gemma."),
    _tool("run_gemma_agent", "Run one supervised session on the tinycalc fixture with the local Gemma "
          "endpoint. Returns an error explaining what is missing if the endpoint or model tag is not ready."),
    _tool("list_agent_runs", "Recent supervised agent runs from the local run log.", {"last": _I}),
    _tool("show_agent_run", "Step-by-step events of one supervised run.", {"run_id": _S}, ["run_id"]),
    _tool("agent_metrics", "Checkpoint metrics over the supervised runs.", {"config": _S}),
    _tool("record_score", "Queue a new leaderboard score for the human to approve. Writes nothing itself.",
          {"version": _S, "public_score": _N, "kaggle_run_id": _S, "submitted_utc": _S, "change": _S,
           "notes": _S}, ["version", "public_score"]),
]


def _explain(version: str) -> dict:
    return {**actions.replay_decision(version),
            "log_notes": [e["text"] for e in actions.log_entries(version, limit=3)]}


HANDLERS: dict[str, Callable[..., Any]] = {
    "factory_status": lambda: actions.status(),
    "list_gate_runs": actions.gate_runs,
    "list_leaderboard": actions.leaderboard,
    "list_candidates": lambda: {"candidates": actions.candidates(), "queue": actions.queue()},
    "explain_candidate": _explain,
    "search_log": actions.log_entries,
    "read_decisions": actions.decisions,
    "read_lessons": actions.lessons,
    "read_goals": actions.goals,
    "noise_evidence": actions.noise,
    "decision_rule_what_if": actions.what_if,
    "judge_gate_log": lambda log_text=None, candidate=None, baseline="V8":
        actions.judge_gate_log(log_text, candidate, baseline),
    "run_tests": actions.run_tests,
    "run_safety_eval": actions.run_safety_eval,
    "build_submission": actions.build_submission,
    "run_scripted_agent": actions.run_scripted_agent,
    "run_gemma_agent": actions.run_gemma_agent,
    "list_agent_runs": actions.agent_runs,
    "show_agent_run": actions.agent_run,
    "agent_metrics": actions.agent_metrics,
}


@dataclass
class Reply:
    text: str
    steps: list[dict] = field(default_factory=list)    # {"name", "input", "result"}
    pending: list[dict] = field(default_factory=list)  # writes awaiting human approval
    mode: str = "claude"
    error: str | None = None


def call_action(name: str, args: dict, pending: list[dict]) -> Any:
    """Run one action by tool name. Errors come back as data so the model can report them."""
    if name == "record_score":
        pending.append({"action": "record_score", "args": args})
        return {"queued_for_human_approval": True, "written": False, "entry": args}
    if name not in HANDLERS:
        return {"error": f"unknown action {name}"}
    try:
        return HANDLERS[name](**args)
    except Exception as e:  # a failed action is a result to report, not a crash
        return {"error": f"{type(e).__name__}: {e}"}


def claude_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


class ClaudeOperator:
    """Multi-turn chat. Keeps the full message history, including tool and thinking blocks."""

    def __init__(self, model: str = MODEL):
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = model
        self.messages: list[dict] = []

    def _create(self):
        return self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
            thinking={"type": "adaptive"},
            output_config={"effort": "medium"},
            tools=TOOLS,
            messages=self.messages,
            # If the model declines a request on policy grounds, the API retries it on a fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

    def ask(self, text: str, on_step: Callable[[dict], None] | None = None) -> Reply:
        a = self._anthropic
        start = len(self.messages)
        self.messages.append({"role": "user", "content": text})
        reply = Reply(text="")
        try:
            for _ in range(MAX_TURNS):
                resp = self._create()
                self.messages.append({"role": "assistant", "content": resp.content})
                if resp.stop_reason == "refusal":
                    reply.text = "The model declined this request."
                    return reply
                if resp.stop_reason != "tool_use":
                    reply.text = "\n\n".join(b.text for b in resp.content if b.type == "text").strip()
                    if resp.stop_reason == "max_tokens":
                        reply.text += "\n\n(The reply was cut off at the output limit.)"
                    return reply
                results = []
                for block in resp.content:
                    if block.type != "tool_use":
                        continue
                    out = call_action(block.name, dict(block.input), reply.pending)
                    step = {"name": block.name, "input": dict(block.input), "result": out}
                    reply.steps.append(step)
                    if on_step:
                        on_step(step)
                    body = json.dumps(out, default=str)
                    if len(body) > RESULT_LIMIT:
                        body = body[:RESULT_LIMIT] + f'\n[truncated: {len(body)} characters in total]'
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": body,
                                    "is_error": isinstance(out, dict) and "error" in out})
                self.messages.append({"role": "user", "content": results})
            reply.text = "Stopped after too many steps without a final answer."
            return reply
        except a.AuthenticationError:
            err = "The Anthropic credentials were rejected."
        except a.RateLimitError:
            err = "Rate limited by the Anthropic API. Try again in a moment."
        except a.APIStatusError as e:
            err = f"Anthropic API error {e.status_code}: {e.message}"
        except a.APIConnectionError:
            err = "Could not reach the Anthropic API."
        del self.messages[start:]  # drop the failed exchange so the history stays valid
        reply.error = err
        return reply


# --------------------------------------------------------------------- offline fallback

def _table(rows: list[dict], cols: list[str]) -> str:
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols)
    return head + "".join("\n| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows)


def _fmt_status(s: dict) -> str:
    q = "; ".join(f"{i['position']}. {i['change']}" for i in s["next_in_queue"])
    warn = "".join(f"\n- {w}" for w in s["warnings"]) or "\n- none"
    return (f"Base is **{s['base']}**, best public score **{s['best_public_score']}** ({s['best_version']}). "
            f"{s['days_to_deadline']} days to the deadline ({s['deadline']}).\n\n"
            f"- Gated candidates: {s['candidates_gated']}; held: {', '.join(s['held'])}\n"
            f"- Last gate run: {s['last_gate_run']}\n- Due today: {s['due_today']}\n- Next in queue: {q}\n\n"
            f"**Warnings**{warn}")


def _fmt_explain(r: dict) -> str:
    if "error" in r:
        return f"{r['error']}. Known candidates: {', '.join(r.get('candidates', []))}."
    why = "; ".join(r["reasons"]) or "passed every check"
    return (f"**{r['version']}: {r['verdict']}** (recorded at the time: {r['recorded_verdict']}).\n\n"
            f"- The one change: {r['the_one_change']}\n"
            f"- In-budget solves per 30: {r['candidate_in_budget']} vs {r['base']} {r['baseline_in_budget']} "
            f"(mean {r['baseline_mean']}), delta {r['delta']:+}\n"
            f"- Paired wins minus losses: {r['paired_net']}\n- Rule: {why}\n\n"
            f"Gate noise is about ±{actions.GATE_NOISE_TASKS} tasks per 30, so a gap this size is not evidence.")


def _fmt_rule(r: dict) -> str:
    if "error" in r:
        return r["error"]
    why = "; ".join(r["reasons"]) or "passed every check"
    return f"**{r['verdict']}**, delta {r['delta']:+}. {why}."


OFFLINE_HELP = ("Offline mode understands: `status`, `gate runs`, `leaderboard`, `queue`, `why V17`, `noise`, "
                "`goals`, `lessons`, `decisions`, `decision 4`, `what if 9 8 net 1`, `judge sample log`, "
                "`run tests`, `run safety eval`, `build`, `run scripted agent`, `agent runs`, `search <words>`.")


class OfflineOperator:
    """Keyword router over the same actions. No model, no network."""

    def ask(self, text: str, on_step: Callable[[dict], None] | None = None) -> Reply:
        t = text.lower().strip()
        reply = Reply(text="", mode="offline")

        def do(name: str, **args) -> Any:
            out = call_action(name, args, reply.pending)
            step = {"name": name, "input": args, "result": out}
            reply.steps.append(step)
            if on_step:
                on_step(step)
            return out

        version = re.search(r"\bv(\d+)\b", t)
        nums = [int(n) for n in re.findall(r"-?\d+", t)]
        if "what if" in t and nums:
            net = re.search(r"net\s*(-?\d+)", t)
            runs = nums[:-1] if net else nums
            reply.text = _fmt_rule(do("decision_rule_what_if", in_budget_runs=runs,
                                      **({"paired_net_run_b": int(net.group(1))} if net else {})))
        elif version and re.search(r"why|held|hold|explain|verdict", t):
            reply.text = _fmt_explain(do("explain_candidate", version=f"V{version.group(1)}"))
        elif "decision" in t:
            n = nums[0] if nums else None
            d = do("read_decisions", **({"number": n} if n else {}))
            reply.text = d[0]["text"] if n and d else _table(d, ["number", "title", "status"])
        elif "run" in t and "test" in t:
            r = do("run_tests")
            reply.text = f"Tests {'passed' if r['ok'] else 'FAILED'}: `{r.get('summary', '')}`"
        elif "safety" in t:
            s = do("run_safety_eval").get("summary", {})
            reply.text = (f"Safety eval {'passed' if s.get('passed') else 'did not pass'}: block rate "
                          f"{s.get('block_rate')}, false-positive rate {s.get('false_positive_rate')}, "
                          f"test-file changes {s.get('test_file_changes')}.")
        elif "build" in t:
            r = do("build_submission")
            reply.text = _table(r["hashes"], ["file", "sha256"]) + (f"\n\n{r['warning']}" if r["warning"] else "")
        elif "scripted" in t:
            r = do("run_scripted_agent")
            reply.text = (f"Scripted run `{r.get('run_id')}` finished **{r.get('status')}** in the "
                          f"{r.get('sandbox')} sandbox. This is a stand-in model, not Gemma.")
        elif "gemma" in t and "run" in t:
            r = do("run_gemma_agent")
            reply.text = r.get("why") or r.get("error") or f"Run `{r.get('run_id')}`: **{r.get('status')}**"
        elif "agent" in t or "session" in t:
            rows = do("list_agent_runs")
            reply.text = _table(rows, ["run_id", "model", "status", "calls", "blocked"]) if rows else \
                "No supervised runs logged yet. Try `run scripted agent`."
        elif "judge" in t or "sample" in t:
            r = do("judge_gate_log")
            reply.text = (f"Synthetic sample log, {r['candidate']} vs {r['baseline']}: in-budget {r['in_budget']}, "
                          f"paired net {r['paired_net']}. " + _fmt_rule(r))
        elif "gate" in t:
            reply.text = _table(do("list_gate_runs"), ["gate_run", "date", "baseline", "candidate", "solved",
                                                       "in_budget", "empty_diff", "paired_net_vs_baseline", "verdict"])
        elif "leaderboard" in t or "score" in t:
            reply.text = _table(do("list_leaderboard"), ["version", "public_score", "change", "notes"])
        elif "queue" in t or "next" in t or "candidate" in t:
            reply.text = _table(do("list_candidates")["queue"], ["position", "change"])
        elif "noise" in t:
            n = do("noise_evidence")
            same = "; ".join(f"{k} {v['runs']}" for k, v in n["same_config_in_budget_solves"].items())
            reply.text = (f"Same config, repeated gate runs (in-budget solves per 30): {same}. "
                          f"{n['leaderboard_evidence']}")
        elif "goal" in t or "okr" in t:
            reply.text = _table(do("read_goals"), ["objective", "key_result", "status"])
        elif "lesson" in t:
            reply.text = do("read_lessons")
        elif t.startswith("search "):
            hits = do("search_log", query=text[7:])
            reply.text = "\n\n".join(f"**{h['title']}**" for h in hits) or "No log entries match."
        elif re.search(r"status|where|check|deadline|due|today", t):
            reply.text = _fmt_status(do("factory_status"))
        else:
            reply.text = "I did not recognise that. " + OFFLINE_HELP
        return reply


def make_operator(prefer_claude: bool = True):
    return ClaudeOperator() if prefer_claude and claude_available() else OfflineOperator()
