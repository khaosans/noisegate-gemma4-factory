"""Factory Console: a Streamlit demo of the software factory and its operator chatbot.

    streamlit run factory_console/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from factory_console import actions  # noqa: E402
from factory_console.chat import ClaudeOperator, OfflineOperator, OFFLINE_HELP, claude_available  # noqa: E402

# Chart colours: fixed by role, never by rank. Validated palette from the dataviz reference (light).
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#e34948")
INK, MUTED, GRID, BAND = "#0b0b0b", "#52514e", "#e6e5e0", "#efeee9"
ROLE = alt.Scale(domain=["baseline", "candidate"], range=[BLUE, ORANGE])
OUTCOMES = ["Solved in budget", "Solved over budget", "Empty diff", "Edit failed", "Logic mismatch", "Timeout"]
OUTCOME_SCALE = alt.Scale(domain=OUTCOMES, range=[BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN])

st.set_page_config(page_title="Factory Console", page_icon="🏭", layout="wide")


def themed(chart: alt.Chart, height: int | dict = 260) -> alt.Chart:
    return (chart.properties(height=height)
            .configure_view(stroke=None)
            .configure_axis(gridColor=GRID, domainColor=GRID, tickColor=GRID, labelColor=MUTED,
                            titleColor=MUTED, labelFontSize=12, titleFontSize=12)
            .configure_legend(labelColor=MUTED, titleColor=MUTED, labelFontSize=12, orient="top", title=None))


def verdict_badge(verdict: str) -> str:
    return f":green-badge[✓ {verdict}]" if verdict.startswith("SUBMIT") else f":orange-badge[■ {verdict}]"


def runs_frame() -> pd.DataFrame:
    df = pd.DataFrame(actions.gate_runs())
    df["role"] = (df["candidate"] == df["baseline"]).map({True: "baseline", False: "candidate"})
    df["run"] = df["gate_run"] + " · " + df["date"].str[5:]
    return df


def delta_chart(delta: float, bars: dict | None = None) -> alt.Chart:
    """Where a delta sits against single-run noise and the two submit bars."""
    bars = bars or {"tier_2": 1.0, "tier_1": 2.5}
    band = alt.Chart(pd.DataFrame([{"a": -3, "b": 3}])).mark_rect(color=BAND).encode(x="a:Q", x2="b:Q")
    lines = pd.DataFrame([{"x": bars["tier_2"], "label": "Tier 2 bar +1.0", "row": 128},
                          {"x": bars["tier_1"], "label": "Tier 1 bar +2.5", "row": 112}])
    rules = alt.Chart(lines).mark_rule(color=MUTED, strokeDash=[4, 3]).encode(x="x:Q")
    rule_text = alt.Chart(lines).mark_text(align="left", dx=4, baseline="top", color=MUTED, fontSize=11).encode(
        x="x:Q", y=alt.Y("row:Q", scale=alt.Scale(domain=[0, 130]), axis=None), text="label:N")
    band_text = alt.Chart(pd.DataFrame([{"x": -3, "t": "single-run noise ±3", "row": 4}])).mark_text(
        align="left", dx=4, baseline="bottom", color=MUTED, fontSize=11).encode(
        x="x:Q", y=alt.Y("row:Q", scale=alt.Scale(domain=[0, 130]), axis=None), text="t:N")
    dot = alt.Chart(pd.DataFrame([{"x": delta, "t": f"Δ {delta:+.1f}"}]))
    point = dot.mark_point(size=260, filled=True, color=ORANGE, opacity=1).encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=[-6, 6]), axis=alt.Axis(tickMinStep=1), title="Candidate mean − baseline mean (in-budget solves per 30)"),
        tooltip=[alt.Tooltip("x:Q", title="delta")])
    label = dot.mark_text(dy=-16, color=INK, fontSize=13, fontWeight="bold").encode(x="x:Q", text="t:N")
    return themed(band + rules + rule_text + band_text + point + label, height=200)


# ----------------------------------------------------------------------------- pages

def page_loop() -> None:
    s = actions.status()
    st.title("A factory that builds a coding agent")
    st.markdown(
        "The **product** is a Gemma 4 agent that fixes GitHub issues in 28 tool calls. The **factory** is the "
        "loop around it: propose one change, measure it on the benchmark, and ship only if the gain is "
        "bigger than the noise. This console reads the factory's own records in this repository.")
    c = st.columns(4)
    c[0].metric("Best public score", s["best_public_score"], help=f"{s['best_version']}, the current base")
    c[1].metric("Candidates gated", s["candidates_gated"])
    c[2].metric("Held by the gate", len(s["held"]), help=", ".join(s["held"]))
    c[3].metric("Days to deadline", s["days_to_deadline"], help=s["deadline"])

    if True:
        st.subheader("The loop")
        st.graphviz_chart("""
digraph {
  rankdir=LR; bgcolor="transparent"; nodesep=0.25; ranksep=0.3;
  node [shape=box, style="rounded,filled", fillcolor="#ffffff", color="#c9c8c2", fontname="Helvetica", fontsize=18, margin="0.14,0.1"];
  edge [color="#8b8a84", fontname="Helvetica", fontsize=14, fontcolor="#52514e"];
  queue [label="Queue\\none change each"];
  build [label="Build candidate\\nbase + 1 change"];
  gate  [label="Eval Gate\\n30 tasks, 2 runs"];
  rule  [label="Decision rule\\ncode + tests", fillcolor="#fdebe3", color="#eb6834"];
  hold  [label="HOLD\\nno submission"];
  submit [label="Submit, then score\\n≤ 1 per week", fillcolor="#e4eefb", color="#2a78d6"];
  human [label="Humans decide\\nbase · cadence · final picks", shape=note, fillcolor="#f6f5f1"];
  queue -> build -> gate -> rule;
  rule -> hold [label="below bar"];
  rule -> submit [label="passes"];
  submit -> queue [label="new base if score ≥ best", constraint=false];
  hold -> queue [constraint=false];
  human -> submit [style=dashed];
  human -> build [style=dashed];
}""", use_container_width=True)
        st.caption("Dashed lines are human decisions. The console can run every local step; starting a Kaggle "
                   "gate run and submitting stay with the team.")
    st.subheader("Where it stands")
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(f"**Due today:** {s['due_today']}")
        st.markdown("**Next in the queue**")
        for item in s["next_in_queue"]:
            st.markdown(f"{item['position']}. {item['change']}")
    with right:
        if s["warnings"]:
            st.markdown("**Needs attention**")
            for w in s["warnings"]:
                st.warning(w, icon="⚠️")


def page_turn() -> None:
    st.title("One turn of the loop")
    st.markdown("Pick a candidate and follow it through the factory, from the one change to the verdict.")
    names = sorted({r["candidate"] for r in actions.gate_runs() if r["candidate"] != r["baseline"]},
                   key=lambda v: int(v[1:]))
    version = st.segmented_control("Candidate", names, default="V17") or "V17"
    r = actions.replay_decision(version)
    row, base_row = r["gate_rows"][-1], next(b for b in r["baseline_rows"] if b["gate_run"] == r["gate_rows"][-1]["gate_run"])

    st.subheader("1 · Build: the base plus exactly one change")
    st.markdown(f"**{version} = {r['base']} +** {r['the_one_change']}")

    st.subheader("2 · Eval Gate: same 30 tasks, same run")
    left, right = st.columns([2, 3], gap="large")
    pair = pd.DataFrame([
        {"config": f"{r['base']} (baseline)", "role": "baseline", "in_budget": base_row["in_budget"], "solved": base_row["solved"]},
        {"config": f"{version} (candidate)", "role": "candidate", "in_budget": row["in_budget"], "solved": row["solved"]}])
    bars = alt.Chart(pair).mark_bar(size=34, cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        y=alt.Y("config:N", sort=None, title=None), x=alt.X("in_budget:Q", scale=alt.Scale(domain=[0, 30]),
                                                            title="In-budget solves out of 30"),
        color=alt.Color("role:N", scale=ROLE, legend=None),
        tooltip=[alt.Tooltip("config:N"), alt.Tooltip("in_budget:Q", title="in-budget solves"),
                 alt.Tooltip("solved:Q", title="solved at any cost")])
    labels = alt.Chart(pair).mark_text(align="left", dx=6, color=INK, fontSize=13).encode(
        y=alt.Y("config:N", sort=None), x="in_budget:Q", text="in_budget:Q")
    left.altair_chart(themed(bars + labels, height=150), use_container_width=True)
    left.caption(f"Gate {row['gate_run']}, {row['date']}. In budget means solved within 28 calls and 480 s.")
    modes = pd.DataFrame([
        {"Outcome (per 30)": lab, r["base"]: base_row[k], version: row[k]} for lab, k in
        [("Solved at any cost", "solved"), ("Solved in budget", "in_budget"), ("Empty diff", "empty_diff"),
         ("Edit failed", "edit_fail"), ("Logic mismatch", "logic_mismatch"), ("Timeout", "timeout"),
         ("Runs over 28 calls", "over_28_calls")]])
    right.dataframe(modes, hide_index=True, use_container_width=True)

    st.subheader("3 · Decision rule: is the gain bigger than the noise?")
    st.altair_chart(delta_chart(r["delta"], r["bars"]), use_container_width=True)
    c = st.columns(4)
    c[0].metric(f"{version} in-budget", ", ".join(map(str, r["candidate_in_budget"])))
    c[1].metric(f"{r['base']} mean over {len(r['baseline_in_budget'])} runs", r["baseline_mean"],
                help=f"runs: {r['baseline_in_budget']}")
    c[2].metric("Delta", f"{r['delta']:+}")
    c[3].metric("Paired wins − losses", "—" if r["paired_net"] is None else f"{r['paired_net']:+}")

    st.subheader("4 · Verdict")
    st.markdown(f"### {verdict_badge(r['verdict'])}")
    for reason in r["reasons"]:
        st.markdown(f"- {reason}")
    st.caption(f"Recorded at the time: {r['recorded_verdict']}. {r['note']}")
    notes = actions.log_entries(version, limit=3)
    if notes:
        with st.expander("What the factory wrote in its log"):
            for n in notes:
                st.markdown(f"**{n['title']}**\n\n" + n["text"].split("\n", 1)[-1])


def page_noise() -> None:
    st.title("Most differences are noise")
    st.markdown("The factory's main finding. The same config, run twice, moves by as much as the changes "
                "we were trying to measure.")
    df = runs_frame()
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Same config, different run")
        base = df[df["role"] == "baseline"]
        line = alt.Chart(base).mark_line(color=BLUE, strokeWidth=2).encode(
            x=alt.X("run:N", sort=None, title="Gate run", axis=alt.Axis(labelAngle=0, labelOverlap=False)),
            y=alt.Y("in_budget:Q", scale=alt.Scale(domain=[0, 14]), title="In-budget solves out of 30"),
            detail="candidate:N", xOffset=alt.value(-18))
        pts = alt.Chart(df).mark_point(size=110, filled=True, opacity=1, stroke="white", strokeWidth=2).encode(
            x=alt.X("run:N", sort=None), y="in_budget:Q", color=alt.Color("role:N", scale=ROLE),
            xOffset=alt.XOffset("role:N", scale=alt.Scale(domain=["baseline", "candidate"], range=[-18, 18])),
            tooltip=[alt.Tooltip("candidate:N", title="config"), alt.Tooltip("run:N"),
                     alt.Tooltip("in_budget:Q", title="in-budget solves"), alt.Tooltip("verdict:N")])
        text = alt.Chart(df).mark_text(dx=12, align="left", color=INK, fontSize=12).encode(
            x=alt.X("run:N", sort=None), y="in_budget:Q", text="candidate:N",
            xOffset=alt.XOffset("role:N", scale=alt.Scale(domain=["baseline", "candidate"], range=[-18, 18])))
        st.altair_chart(themed(line + pts + text, height=300), use_container_width=True)
        n = actions.noise()["same_config_in_budget_solves"]
        st.caption("Lines join repeat runs of one baseline config: " +
                   "; ".join(f"{k} scored {v['runs'][0]} then {v['runs'][1]}" for k, v in n.items()) +
                   ". No candidate beat its baseline by more than that.")
    with right:
        st.subheader("Leaderboard: ±0.05 on an identical config")
        lb = pd.DataFrame(actions.leaderboard())
        lb["lo"], lb["hi"] = lb["public_score"] - actions.LEADERBOARD_NOISE, lb["public_score"] + actions.LEADERBOARD_NOISE
        bars = alt.Chart(lb).mark_bar(size=30, color=BLUE, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("version:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("public_score:Q", scale=alt.Scale(domain=[0, 0.3]), title="Public score"),
            tooltip=[alt.Tooltip("version:N"), alt.Tooltip("public_score:Q", title="score"),
                     alt.Tooltip("change:N"), alt.Tooltip("notes:N")])
        err = alt.Chart(lb).mark_rule(color=INK, strokeWidth=1.5).encode(
            x=alt.X("version:N", sort=None), y="lo:Q", y2="hi:Q")
        val = alt.Chart(lb).mark_text(dx=24, color=INK, fontSize=12).encode(
            x=alt.X("version:N", sort=None), y="public_score:Q", text=alt.Text("public_score:Q", format=".2f"))
        ref = alt.Chart(pd.DataFrame([{"y": 0.22, "t": "0.22: the public notebook V15 copies"}]))
        st.altair_chart(themed(bars + err + val + ref.mark_rule(color=MUTED, strokeDash=[4, 3]).encode(y="y:Q")
                               + ref.mark_text(align="left", dx=-250, dy=-8, color=MUTED, fontSize=11).encode(
                                   y="y:Q", x=alt.value(260), text="t:N"), height=300), use_container_width=True)
        st.caption("Whiskers are ±0.05. V15 is an exact copy of a public 0.22 config and scored 0.17, so every "
                   "score here overlaps V8's.")

    st.subheader("What happened to each of the 30 tasks")
    long = []
    for _, r in df.iterrows():
        parts = {"Solved in budget": r["in_budget"], "Solved over budget": r["solved"] - r["in_budget"],
                 "Empty diff": r["empty_diff"], "Edit failed": r["edit_fail"],
                 "Logic mismatch": r["logic_mismatch"], "Timeout": r["timeout"]}
        long += [{"row": f"{r['run']} · {r['candidate']}", "outcome": k, "tasks": v, "order": i}
                 for i, (k, v) in enumerate(parts.items())]
    stack = alt.Chart(pd.DataFrame(long)).mark_bar(size=18, stroke="white", strokeWidth=2).encode(
        y=alt.Y("row:N", sort=None, title=None), x=alt.X("tasks:Q", scale=alt.Scale(domain=[0, 30]), title="Tasks"),
        color=alt.Color("outcome:N", scale=OUTCOME_SCALE, sort=OUTCOMES), order="order:Q",
        tooltip=[alt.Tooltip("row:N", title="run"), alt.Tooltip("outcome:N"), alt.Tooltip("tasks:Q")])
    st.altair_chart(themed(stack, height={"step": 30}), use_container_width=True)
    st.caption("Only the first segment counts. Empty diffs are the agent reading until the budget runs out.")
    with st.expander("Table view"):
        st.dataframe(df.drop(columns=["role", "run"]), hide_index=True, use_container_width=True)


def page_rule() -> None:
    st.title("The decision rule")
    st.markdown("The rule lives in `harness/decision_rule.py` with tests, so the loop cannot talk itself into a "
                "submission. Move the numbers and watch the verdict. The baseline is V8's recorded history.")
    left, right = st.columns([2, 3], gap="large")
    with left:
        a = st.slider("Run A: candidate in-budget solves", 0, 30, 9)
        two = st.toggle("Second run (Run B)", value=True)
        b = st.slider("Run B: candidate in-budget solves", 0, 30, 8, disabled=not two)
        net = st.slider("Run B paired wins − losses", -6, 6, 1, disabled=not two)
        empty = st.slider("Empty diffs per run", 0, 30, 8)
        over = st.slider("Runs over budget per run", 0, 30, 17)
        with st.expander("Hard checks"):
            tests = st.checkbox("Edited test files")
            harness = st.checkbox("Harness error or stopped early")
            sha = st.checkbox("Zip SHA-256 matches", value=True)
            one = st.checkbox("Exactly one change off the base", value=True)
            fresh = st.checkbox("Config never scored before", value=True)
    r = actions.what_if([a, b] if two else [a], net if two else None, empty, over, tests, harness, sha, one, fresh)
    with right:
        st.markdown(f"### {verdict_badge(r['verdict'])}")
        for reason in r["reasons"]:
            st.markdown(f"- {reason}")
        st.altair_chart(delta_chart(r["delta"]), use_container_width=True)
        c = st.columns(3)
        c[0].metric("Candidate mean", r["candidate_mean"])
        c[1].metric("V8 mean", r["v8_mean"], help=f"runs: {r['v8_runs']}")
        c[2].metric("Delta", f"{r['delta']:+}")
        st.caption("Tier 2 needs +1.0 over two runs with a non-negative paired net; Tier 1 needs +2.5. Both bars "
                   "sit inside single-run noise, which is why one run is never enough.")


def page_log() -> None:
    st.title("Judge a gate log")
    st.markdown("Paste the Eval Gate notebook's output. The parser dedupes the `Score` lines, counts in-budget "
                "solves, pairs tasks between the two configs, and applies the rule.")
    sample = actions.SAMPLE_LOG.read_text()
    text = st.text_area("Gate log", value=sample, height=180)
    is_sample = text.strip() == sample.strip()
    if is_sample:
        st.info("This is a synthetic 8-task sample written for the demo, not a real gate run.", icon="ℹ️")
    c = st.columns(2)
    baseline = c[0].text_input("Baseline name", "V8")
    candidate = c[1].text_input("Candidate name (blank = the other one)", "")
    r = actions.judge_gate_log(text, candidate.strip() or None, baseline.strip())
    if "error" in r:
        st.error(r["error"])
        return
    m = st.columns(4)
    m[0].metric(f"{r['candidate']} in-budget", f"{r['in_budget'][r['candidate']]} / {r['tasks_per_candidate']}")
    m[1].metric(f"{r['baseline']} in-budget", f"{r['in_budget'][r['baseline']]} / {r['tasks_per_candidate']}")
    m[2].metric("Paired wins − losses", f"{r['paired_net']:+}")
    m[3].markdown(f"### {verdict_badge(r['verdict'])}")
    for reason in r["reasons"]:
        st.markdown(f"- {reason}")

    df = pd.DataFrame(r["tasks"])
    df["outcome"] = df.apply(lambda t: "Solved in budget" if t["in_budget_solve"] else
                             "Solved over budget" if t["solved"] else "Not solved", axis=1)
    grid_scale = alt.Scale(domain=["Solved in budget", "Solved over budget", "Not solved"], range=[BLUE, ORANGE, BAND])
    cells = alt.Chart(df).mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        x=alt.X("task:N", sort=None, title=None, axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("candidate:N", title=None), color=alt.Color("outcome:N", scale=grid_scale),
        tooltip=[alt.Tooltip("candidate:N", title="config"), alt.Tooltip("task:N"), alt.Tooltip("mode:N"),
                 alt.Tooltip("calls:Q"), alt.Tooltip("dur_s:Q", title="seconds"),
                 alt.Tooltip("first_edit:Q", title="first edit at call")])
    calls = alt.Chart(df).mark_text(color=INK, fontSize=12).encode(
        x=alt.X("task:N", sort=None), y="candidate:N", text="calls:Q")
    st.subheader("Task grid")
    st.altair_chart(themed(cells + calls, height=230), use_container_width=True)
    st.caption("Numbers are tool calls used. A solve past 28 calls or 480 s does not count.")
    with st.expander("Evaluator pass rates (E1–E9)"):
        st.dataframe(pd.DataFrame(r["scorecard"]), use_container_width=True)


def page_sessions() -> None:
    st.title("Agent sessions")
    st.markdown("One agent run, call by call, through the supervisor: every tool call is checked by the "
                "guardrails and counted against the 28-call budget before it executes.")
    ready = actions.gemma_ready()
    c = st.columns([1, 1, 3])
    if c[0].button("Run scripted session", help="A scripted stand-in model, not Gemma"):
        with st.spinner("Running in the sandbox…"):
            st.session_state.last_session = actions.run_scripted_agent()
    if c[1].button("Run Gemma session", disabled=not ready["ready"]):
        with st.spinner("Gemma is working…"):
            st.session_state.last_session = actions.run_gemma_agent()
    if not ready["ready"]:
        c[2].caption(f"Gemma is not available: {ready['why']}. Start Ollama, pull a Gemma tag that supports "
                     "tool calling, and set NOISEGATE_MODEL.")
    runs = actions.agent_runs(50)
    if not runs:
        st.info("No sessions logged yet. Run the scripted session to see the supervisor and guardrails work.")
        return
    labels = {f"{r['run_id']} · {r['model']} · {r['status']}": r for r in reversed(runs)}
    run = labels[st.selectbox("Session", list(labels))]
    if run["model"] == "scripted":
        st.info("Scripted stand-in model. This shows the supervisor and guardrails, not Gemma's behaviour.", icon="ℹ️")
    m = st.columns(5)
    m[0].metric("Status", run["status"])
    m[1].metric("Calls used", f"{run['calls']} / 28")
    m[2].metric("First edit at call", run["first_edit_call"] or "—")
    m[3].metric("Blocked calls", run["blocked"] or 0)
    m[4].metric("Tests passed", "yes" if run["tests_passed"] else "no")

    events = actions.agent_run(run["run_id"]).get("events", [])
    calls = [e for e in events if e["kind"] == "tool_call"]
    slots = [{"slot": i, "row": "calls", "tool": "", "state": "unused", "reason": "", "args": ""} for i in range(1, 29)]
    for i, e in enumerate(calls[:28]):
        slots[i].update(tool=e["tool"], state="allowed" if e["verdict"] == "allow" else "blocked",
                        reason=e["reason"], args=str(e["args"])[:160])
    ruler = pd.DataFrame(slots)
    scale = alt.Scale(domain=["allowed", "blocked", "unused"], range=[BLUE, RED, BAND])
    cells = alt.Chart(ruler).mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        x=alt.X("slot:O", title="Tool call (budget 28)", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("row:N", axis=None), color=alt.Color("state:N", scale=scale),
        tooltip=[alt.Tooltip("slot:O", title="call"), alt.Tooltip("tool:N"), alt.Tooltip("state:N"),
                 alt.Tooltip("reason:N"), alt.Tooltip("args:N")])
    names = alt.Chart(ruler).mark_text(color="white", fontSize=11, fontWeight="bold").encode(x="slot:O", y=alt.Y("row:N", axis=None), text="tool:N")
    st.altair_chart(themed(cells + names, height=200), use_container_width=True)
    st.caption("Blocked calls are stopped by the guardrails before they run; here, an attempt to edit a test file.")
    table = [{"call": i + 1, "tool": e["tool"], "guard": e["verdict"], "reason": e["reason"],
              "args": str(e["args"])[:140]} for i, e in enumerate(calls)]
    st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
    last = st.session_state.get("last_session")
    if last and last.get("run_id") == run["run_id"] and last.get("diff"):
        st.subheader("Patch")
        st.code(last["diff"], language="diff")


SUGGESTIONS = ["Where does the factory stand today?", "Why was V17 held?",
               "Would 9 and 8 in-budget solves with paired net +1 ship?", "Run the tests", "What is next in the queue?"]


def page_chat() -> None:
    st.title("Operator chat")
    ss = st.session_state
    ss.setdefault("chat", [])
    ss.setdefault("pending", [])
    use_claude = claude_available() and not ss.get("claude_failed")
    if "operator" not in ss:
        ss.operator = ClaudeOperator() if use_claude else OfflineOperator()
    offline = isinstance(ss.operator, OfflineOperator)
    st.caption("Ask about the factory, or ask it to run a local job. It works through the same actions as the "
               "other pages and cannot start a gate run, submit, or change the base. "
               + ("**Offline mode** (no working Anthropic credentials): keyword commands only."
                  if offline else f"Model: `{ss.operator.model}`."))

    for i, p in enumerate(list(ss.pending)):
        with st.container(border=True):
            st.markdown(f"**Waiting for your approval:** record `{p['args'].get('version')}` at "
                        f"`{p['args'].get('public_score')}` in `results/leaderboard.csv`")
            a, b, _ = st.columns([1, 1, 6])
            if a.button("Approve", key=f"ok{i}", type="primary"):
                out = actions.record_score(**p["args"])
                ss.chat.append({"role": "assistant", "text": f"Recorded: `{out}`" if "error" not in out else out["error"], "steps": []})
                ss.pending.remove(p)
                st.rerun()
            if b.button("Discard", key=f"no{i}"):
                ss.pending.remove(p)
                st.rerun()

    for msg in ss.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["text"])
            if msg.get("steps"):
                with st.expander(f"Actions run ({len(msg['steps'])})"):
                    for s in msg["steps"]:
                        st.markdown(f"`{s['name']}` {s['input'] or ''}")
                        st.json(s["result"], expanded=False)

    picked = None
    if not ss.chat:
        cols = st.columns(len(SUGGESTIONS))
        for col, q in zip(cols, SUGGESTIONS):
            if col.button(q, use_container_width=True):
                picked = q
    prompt = st.chat_input("Ask the factory…" if not offline else "status · why V17 · what if 9 8 net 1 · run tests") or picked
    if not prompt:
        if offline and not ss.chat:
            st.caption(OFFLINE_HELP)
        return
    ss.chat.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.status("Working…", expanded=False) as box:
            def show(step: dict) -> None:
                box.write(f"`{step['name']}` {step['input'] or ''}")
            reply = ss.operator.ask(prompt, on_step=show)
            if reply.error:
                box.write(f"{reply.error} Falling back to offline mode.")
                ss.claude_failed, ss.operator = True, OfflineOperator()
                note, reply = reply.error, ss.operator.ask(prompt, on_step=show)
                reply.text = f"*{note} Answering in offline mode.*\n\n{reply.text}"
            box.update(label=f"{len(reply.steps)} action(s) run", state="complete")
        st.markdown(reply.text)
    ss.pending += reply.pending
    ss.chat.append({"role": "assistant", "text": reply.text, "steps": reply.steps})
    st.rerun()


def page_records() -> None:
    st.title("Records")
    tabs = st.tabs(["Queue and candidates", "Goals", "Decisions", "Lessons", "Factory log"])
    with tabs[0]:
        st.subheader("Queue (base V8)")
        st.dataframe(pd.DataFrame(actions.queue()), hide_index=True, use_container_width=True)
        st.subheader("Candidates so far")
        st.dataframe(pd.DataFrame(actions.candidates()), hide_index=True, use_container_width=True)
    with tabs[1]:
        st.dataframe(pd.DataFrame(actions.goals()), hide_index=True, use_container_width=True)
    with tabs[2]:
        for d in actions.decisions():
            with st.expander(f"{d['title']} — {d['status']}"):
                st.markdown(actions.decisions(d["number"])[0]["text"].split("\n", 1)[-1])
    with tabs[3]:
        st.markdown(actions.lessons())
    with tabs[4]:
        q = st.text_input("Search the log", "")
        for e in actions.log_entries(q or None, limit=30):
            with st.expander(e["title"]):
                st.markdown(e["text"].split("\n", 1)[-1])


nav = st.navigation([
    st.Page(page_loop, title="Factory loop", icon="🏭", url_path="loop", default=True),
    st.Page(page_turn, title="One turn of the loop", icon="🔁", url_path="turn"),
    st.Page(page_noise, title="Noise", icon="📊", url_path="noise"),
    st.Page(page_rule, title="Decision rule", icon="⚖️", url_path="rule"),
    st.Page(page_log, title="Judge a gate log", icon="📋", url_path="log"),
    st.Page(page_sessions, title="Agent sessions", icon="🤖", url_path="sessions"),
    st.Page(page_chat, title="Operator chat", icon="💬", url_path="chat"),
    st.Page(page_records, title="Records", icon="🗂️", url_path="records"),
])
nav.run()
