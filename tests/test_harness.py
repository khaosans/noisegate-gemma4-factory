from harness.decision_rule import RunSummary, V8_HISTORY, decide, load_v8_history, paired_net
from harness.evaluators import scorecard
from harness.trajectory import parse_log

LOG = """\
10:01:02  Score  V8 rich_3043 rep0: SOLVED solved=True calls=17 first_edit=9 malformed=0 dur=301s reads=8 badedits=0 post=0 tok=41000 gold=True src=rich/text.py
10:01:02  Score  V8 rich_3043 rep0: SOLVED solved=True calls=17 first_edit=9 malformed=0 dur=301s reads=8 badedits=0 post=0 tok=41000 gold=True src=rich/text.py
10:09:40  Score  V8 rich_3521 rep0: EMPTY_DIFF solved=False calls=30 first_edit=None malformed=0 dur=470s reads=22 badedits=0 post=0 tok=52000 gold=None src=
10:15:00  Score  C1 rich_3043 rep0: SOLVED solved=True calls=29 first_edit=14 malformed=0 dur=410s reads=10 badedits=1 post=0 tok=60000 gold=True src=rich/text.py
10:21:00  Score  C1 rich_3521 rep0: SOLVED solved=True calls=20 first_edit=8 malformed=0 dur=350s reads=6 badedits=0 post=0 tok=38000 gold=True src=rich/console.py
"""


def test_parse_dedupes_and_types():
    rows = parse_log(LOG.splitlines())
    assert len(rows) == 4
    empty = next(r for r in rows if r.task == "rich_3521" and r.candidate == "V8")
    assert empty.first_edit is None and empty.src == [] and empty.empty_or_nonsource


def test_in_budget_metric_and_paired_net():
    rows = parse_log(LOG.splitlines())
    v8 = [r for r in rows if r.candidate == "V8"]
    c1 = [r for r in rows if r.candidate == "C1"]
    # C1 solves rich_3043 at 29 calls (over budget) -> loss; solves rich_3521 in budget -> win
    assert paired_net(c1, v8) == 0
    assert scorecard(rows)["C1"]["E2 within budget"] == 0.5


# Rule-logic tests pin the original two V8 runs (v1, v4; mean 7.0) so they don't move with the ledger.
V8_V1_V4 = [RunSummary(8, 7, 16), RunSummary(6, 9, 18)]

ok = dict(zip_sha_ok=True, one_change_off_base=True, never_scored=True)


def test_v14_single_run_net_zero_holds():
    # gate v4: V14 6 in-budget, paired net 0 -> one run only, no tier passes
    v14 = [RunSummary(in_budget_solves=6, empty_or_nonsource=6, overruns=16)]
    assert decide(v14, V8_V1_V4, run_b_paired_net=0, **ok).verdict == "HOLD"


def test_tier2_passes():
    cand = [RunSummary(8, 7, 16), RunSummary(9, 7, 16)]  # mean 8.5 vs 7.0 -> +1.5
    d = decide(cand, V8_V1_V4, run_b_paired_net=1, **ok)
    assert d.verdict == "SUBMIT tier 2" and d.delta == 1.5


def test_negative_paired_net_blocks_even_with_delta():
    cand = [RunSummary(11, 7, 16), RunSummary(10, 7, 16)]
    assert decide(cand, V8_V1_V4, run_b_paired_net=-1, **ok).verdict == "HOLD"


def test_more_empty_diffs_blocks():
    cand = [RunSummary(11, 12, 16), RunSummary(10, 12, 16)]  # V8 empty mean 8 -> limit 9
    d = decide(cand, V8_V1_V4, run_b_paired_net=2, **ok)
    assert d.verdict == "HOLD" and "EMPTY_DIFF" in d.reasons[0]


def test_never_resubmit_scored_config():
    cand = [RunSummary(12, 5, 13), RunSummary(11, 5, 13)]
    d = decide(cand, V8_V1_V4, 3, zip_sha_ok=True, one_change_off_base=True, never_scored=False)
    assert d.verdict == "HOLD"


# --- V8 history comes from results/gate_runs.csv (regression for the 2-run drift) ---

def test_v8_history_matches_ledger():
    assert [r.in_budget_solves for r in V8_HISTORY] == [8, 6, 8]  # v1, v4, v8 Run B
    assert round(sum(r.in_budget_solves for r in V8_HISTORY) / len(V8_HISTORY), 2) == 7.33


def test_loader_falls_back_when_ledger_missing(tmp_path):
    assert [r.in_budget_solves for r in load_v8_history(tmp_path / "missing.csv")] == [8, 6, 8]


def test_loader_reads_only_v8_baseline_rows(tmp_path):
    p = tmp_path / "g.csv"
    p.write_text("gate_run,kaggle_run_id,date,baseline,candidate,solved,in_budget,empty_diff,edit_fail,"
                 "logic_mismatch,timeout,over_28_calls,paired_net_vs_baseline,verdict\n"
                 "v1,1,d,V8,V8,9,8,7,2,11,1,16,,baseline\n"
                 "v5,2,d,V15,V15,11,7,8,1,6,4,14,,baseline\n"
                 "v1,1,d,V8,V11,13,10,5,2,8,2,15,,HOLD\n")
    assert [(r.in_budget_solves, r.empty_or_nonsource, r.overruns) for r in load_v8_history(p)] == [(8, 7, 16)]


def test_w46_v18_reproduces_logged_hold():
    # eval-results 2026-11-09: delta -0.33, overrun hard check fails (V18 mean 19.5 > ledger V8 mean 17.0 + 1)
    v18 = [RunSummary(7, 7, 19), RunSummary(7, 5, 20)]
    d = decide(v18, V8_HISTORY, run_b_paired_net=-1, **ok)
    assert d.verdict == "HOLD" and d.delta == -0.33 and "overruns" in d.reasons[0]


def test_w47_v22_single_run_screen_delta():
    # eval-results 2026-11-17: V22 single-run screen, delta +1.67 (old 2-run history gave +2.0)
    d = decide([RunSummary(9, 4, 17)], V8_HISTORY, None, single_run_screen=True, **ok)
    assert d.verdict == "HOLD" and d.delta == 1.67
