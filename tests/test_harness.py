from harness.decision_rule import RunSummary, V8_HISTORY, decide, paired_net
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


ok = dict(zip_sha_ok=True, one_change_off_base=True, never_scored=True)


def test_v14_single_run_net_zero_holds():
    # gate v4: V14 6 in-budget, paired net 0 -> one run only, no tier passes
    v14 = [RunSummary(in_budget_solves=6, empty_or_nonsource=6, overruns=16)]
    assert decide(v14, V8_HISTORY, run_b_paired_net=0, **ok).verdict == "HOLD"


def test_tier2_passes():
    cand = [RunSummary(8, 7, 16), RunSummary(9, 7, 16)]  # mean 8.5 vs 7.0 -> +1.5
    d = decide(cand, V8_HISTORY, run_b_paired_net=1, **ok)
    assert d.verdict == "SUBMIT tier 2" and d.delta == 1.5


def test_negative_paired_net_blocks_even_with_delta():
    cand = [RunSummary(11, 7, 16), RunSummary(10, 7, 16)]
    assert decide(cand, V8_HISTORY, run_b_paired_net=-1, **ok).verdict == "HOLD"


def test_more_empty_diffs_blocks():
    cand = [RunSummary(11, 12, 16), RunSummary(10, 12, 16)]  # V8 empty mean 8 -> limit 9
    d = decide(cand, V8_HISTORY, run_b_paired_net=2, **ok)
    assert d.verdict == "HOLD" and "EMPTY_DIFF" in d.reasons[0]


def test_never_resubmit_scored_config():
    cand = [RunSummary(12, 5, 13), RunSummary(11, 5, 13)]
    d = decide(cand, V8_HISTORY, 3, zip_sha_ok=True, one_change_off_base=True, never_scored=False)
    assert d.verdict == "HOLD"
