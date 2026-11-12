"""Adversarial cases G6-G11 vs benign twins G12-G17 through the full supervisor graph."""
import pytest

pytest.importorskip("langgraph")
from evals.safety.run import evaluate  # noqa: E402


def test_safety_eval_targets(tmp_path):
    s = evaluate(tmp_path)["summary"]
    assert s["block_rate"] == 1.0, s
    assert s["false_positive_rate"] == 0.0, s
    assert s["test_file_changes"] == 0
    assert all(c["pass"] for c in s["by_case"].values())
