from pathlib import Path
import pytest

from harness.plot_gate_band import CSV_PATH, load_candidate_data, plot_gate_band


def test_load_candidate_data():
    assert CSV_PATH.is_file(), f"Missing gate runs CSV: {CSV_PATH}"
    versions, values, verdicts = load_candidate_data(CSV_PATH)

    assert "V8" in versions
    assert "V22" in versions
    assert "V24" in versions
    assert len(versions) == len(values) == len(verdicts)

    # V8 baseline mean should be around 7.33
    v8_val = values[versions.index("V8")]
    assert 7.0 <= v8_val <= 7.5

    # V22 confirmed candidate
    assert values[versions.index("V22")] == 9.0

    # V24 target hypothesis
    assert values[versions.index("V24")] == 12.0
    assert verdicts[versions.index("V24")] == "target"


def test_plot_gate_band_outputs_valid_png(tmp_path: Path):
    out_file = tmp_path / "test_band.png"
    result_path = plot_gate_band(out_path=out_file, csv_path=CSV_PATH)

    assert result_path.is_file()
    assert result_path.stat().st_size > 10_000  # Non-empty valid PNG image
    with result_path.open("rb") as f:
        header = f.read(8)
    assert header == b"\x89PNG\r\n\x1a\n"
