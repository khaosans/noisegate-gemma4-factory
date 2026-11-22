"""Generate deterministic gate noise-band chart from results/gate_runs.csv.

Outputs assets/gate_noise_band.png matching GitHub dark theme.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "results" / "gate_runs.csv"
OUT_PATH = ROOT / "assets" / "gate_noise_band.png"

V8_MEAN = 7.33
BAND_HALF = 2.5
V24_TARGET = 12.0


def load_candidate_data(csv_path: Path = CSV_PATH) -> tuple[list[str], list[float], list[str]]:
    """Read results/gate_runs.csv and return ordered (versions, values, verdicts)."""
    with open(csv_path, newline="") as f:
        rows = list(csv.DictReader(f))

    # Calculate V8 baseline mean
    v8_solves = [float(r["in_budget"]) for r in rows if r["candidate"] == "V8" and r["verdict"].strip() == "baseline"]
    v8_val = round(sum(v8_solves) / len(v8_solves), 2) if v8_solves else V8_MEAN

    # Ordered unique candidates
    version_order = ["V8", "V11", "V12", "V14", "V15", "V16", "V17", "V18", "V19", "V20", "V21", "V22", "V23"]
    
    # Aggregate values and representative verdict per candidate
    cand_values: dict[str, list[float]] = {}
    cand_verdicts: dict[str, str] = {}
    
    for r in rows:
        c = r["candidate"].strip()
        if c in version_order:
            cand_values.setdefault(c, []).append(float(r["in_budget"]))
            cand_verdicts[c] = r["verdict"].strip()
            
    versions = []
    values = []
    verdicts = []
    
    for v in version_order:
        if v == "V8":
            versions.append(v)
            values.append(v8_val)
            verdicts.append("baseline")
        elif v in cand_values:
            versions.append(v)
            # Use mean across runs for the version
            mean_val = round(sum(cand_values[v]) / len(cand_values[v]), 2)
            values.append(mean_val)
            verdicts.append(cand_verdicts.get(v, "HOLD"))

    # Append queued V24 target
    versions.append("V24")
    values.append(V24_TARGET)
    verdicts.append("target")

    return versions, values, verdicts


def plot_gate_band(out_path: Path = OUT_PATH, csv_path: Path = CSV_PATH) -> Path:
    import matplotlib.pyplot as plt

    out_path.parent.mkdir(parents=True, exist_ok=True)
    versions, values, verdicts = load_candidate_data(csv_path)

    # 16:9 aspect ratio at 200 DPI
    fig, ax = plt.subplots(figsize=(16, 9), dpi=200)

    # Backgrounds
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    # V8 noise band & mean line
    band_lower = V8_MEAN - BAND_HALF  # 4.83
    band_upper = V8_MEAN + BAND_HALF  # 9.83
    ax.axhspan(
        band_lower,
        band_upper,
        color="#1f6feb",
        alpha=0.18,
        label="V8 Baseline Noise Band",
        zorder=1,
    )
    ax.axhline(
        V8_MEAN,
        color="#58a6ff",
        linestyle=":",
        linewidth=1.8,
        alpha=0.75,
        zorder=2,
    )

    # Split evaluated vs target
    eval_idx = list(range(len(versions) - 1))
    eval_vals = values[:-1]
    target_idx = [len(versions) - 2, len(versions) - 1]
    target_vals = [values[-2], values[-1]]

    # Solid progression path through V23
    ax.plot(
        eval_idx,
        eval_vals,
        color="#58a6ff",
        linestyle="-",
        linewidth=2.2,
        alpha=0.7,
        zorder=3,
        label="Progression Path",
    )

    # Dashed connector to V24 hypothesis
    ax.plot(
        target_idx,
        target_vals,
        color="#8b949e",
        linestyle="--",
        linewidth=2.0,
        alpha=0.8,
        zorder=3,
    )

    # Plot markers by status
    # Standard HOLD markers (#58a6ff)
    hold_x = [i for i, v in enumerate(verdicts[:-1]) if versions[i] != "V22"]
    hold_y = [values[i] for i in hold_x]
    ax.scatter(
        hold_x,
        hold_y,
        color="#58a6ff",
        s=80,
        zorder=4,
        edgecolors="#0d1117",
        linewidth=1.2,
    )

    # CONFIRM marker (V22) highlighted in #3fb950
    v22_idx = versions.index("V22")
    ax.scatter(
        [v22_idx],
        [values[v22_idx]],
        color="#3fb950",
        s=150,
        zorder=5,
        edgecolors="#ffffff",
        linewidth=1.5,
        label="Confirmed Candidate",
    )

    # V24 Target hollow marker
    v24_idx = versions.index("V24")
    ax.scatter(
        [v24_idx],
        [values[v24_idx]],
        facecolors="none",
        edgecolors="#d29922",
        s=150,
        linewidth=2.4,
        zorder=5,
        label="Target / Hypothesis",
    )

    # Annotations - carefully spaced to eliminate collisions
    bbox_style = dict(boxstyle="round,pad=0.4", facecolor="#161b22", edgecolor="#30363d", alpha=0.95)
    arrow_style = dict(arrowstyle="->", color="#8b949e", lw=1.2)

    # V8 Baseline
    ax.annotate(
        "V8 Baseline\n(7.33 / 30, 0.18 LB)",
        xy=(0, values[0]),
        xytext=(0, values[0] - 2.0),
        fontsize=10.5,
        color="#c9d1d9",
        fontweight="bold",
        ha="center",
        bbox=bbox_style,
        arrowprops=arrow_style,
    )

    # V11 in-band noise
    ax.annotate(
        "V11 (10 / 30 local)\n0.15 LB — in-band noise",
        xy=(1, values[1]),
        xytext=(1.2, values[1] + 1.8),
        fontsize=10,
        color="#e3b341",
        ha="center",
        bbox=bbox_style,
        arrowprops=arrow_style,
    )

    # Noise band boundary labels placed in open regions
    ax.text(
        3.2,
        band_upper + 0.18,
        f"Upper Noise Threshold ({band_upper:.2f} / 30)",
        color="#8b949e",
        fontsize=9.5,
        alpha=0.85,
    )
    ax.text(
        4.0,
        band_lower - 0.45,
        f"Lower Noise Threshold ({band_lower:.2f} / 30)",
        color="#8b949e",
        fontsize=9.5,
        alpha=0.85,
    )
    ax.text(
        -0.5,
        V8_MEAN + 0.15,
        f"V8 Mean ({V8_MEAN:.2f})",
        color="#58a6ff",
        fontsize=9,
        alpha=0.75,
    )

    # V18 HOLD
    v18_idx = versions.index("V18")
    ax.annotate(
        "V18 (HOLD)\nHeredoc recovery",
        xy=(v18_idx, values[v18_idx]),
        xytext=(v18_idx - 0.5, values[v18_idx] + 1.8),
        fontsize=9.5,
        color="#8b949e",
        ha="center",
        bbox=bbox_style,
        arrowprops=arrow_style,
    )

    # V20 HOLD
    v20_idx = versions.index("V20")
    ax.annotate(
        "V20 (HOLD)\n0.13 LB",
        xy=(v20_idx, values[v20_idx]),
        xytext=(v20_idx - 0.2, values[v20_idx] - 1.9),
        fontsize=9.5,
        color="#8b949e",
        ha="center",
        bbox=bbox_style,
        arrowprops=arrow_style,
    )

    # V21 HOLD
    v21_idx = versions.index("V21")
    ax.annotate(
        "V21 (HOLD)\nThink 2k",
        xy=(v21_idx, values[v21_idx]),
        xytext=(v21_idx + 0.3, values[v21_idx] - 2.5),
        fontsize=9.5,
        color="#8b949e",
        ha="center",
        bbox=bbox_style,
        arrowprops=arrow_style,
    )

    # V22 CONFIRM
    ax.annotate(
        "V22 (9 / 30)\nCONFIRM 2nd paired run",
        xy=(v22_idx, values[v22_idx]),
        xytext=(v22_idx, values[v22_idx] + 2.0),
        fontsize=10.5,
        color="#3fb950",
        fontweight="bold",
        ha="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#161b22", edgecolor="#238636", alpha=0.95),
        arrowprops=dict(arrowstyle="->", color="#3fb950", lw=1.5),
    )

    # V23 HOLD
    v23_idx = versions.index("V23")
    ax.annotate(
        "V23 (HOLD)\nGraph tools removed",
        xy=(v23_idx, values[v23_idx]),
        xytext=(v23_idx, values[v23_idx] - 2.6),
        fontsize=9.5,
        color="#8b949e",
        ha="center",
        bbox=bbox_style,
        arrowprops=arrow_style,
    )

    # V24 Target
    ax.annotate(
        "V24 (Target)\nTool-layer read-budget cap",
        xy=(v24_idx, values[v24_idx]),
        xytext=(v24_idx, values[v24_idx] + 1.8),
        fontsize=10.5,
        color="#d29922",
        fontweight="bold",
        ha="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#161b22", edgecolor="#9e6a03", alpha=0.95),
        arrowprops=dict(arrowstyle="->", color="#d29922", lw=1.5),
    )

    # Axes limits, ticks and styling
    ax.set_xlim(-0.7, len(versions) - 0.3)
    ax.set_ylim(2.5, 14.8)
    ax.set_xticks(range(len(versions)))
    ax.set_xticklabels(versions, fontsize=11, color="#c9d1d9")
    ax.tick_params(axis="both", colors="#8b949e", which="both")

    # Titles & Labels
    ax.set_xlabel("Candidate Versions", fontsize=13, color="#c9d1d9", labelpad=12, fontweight="bold")
    ax.set_ylabel("In-Budget Solves (out of 30)", fontsize=13, color="#c9d1d9", labelpad=12, fontweight="bold")
    ax.set_title(
        "NoiseGate Evaluation Band: V8 Baseline vs. Candidate Solves & Noise Rejection",
        fontsize=16,
        color="#f0f6fc",
        fontweight="bold",
        pad=20,
    )

    # Grid & Spines
    ax.grid(True, color="#21262d", linestyle="--", linewidth=0.8, alpha=0.7)
    for spine in ax.spines.values():
        spine.set_color("#30363d")

    # Clean Top-Left Legend
    legend = ax.legend(
        loc="upper left",
        facecolor="#161b22",
        edgecolor="#30363d",
        fontsize=10.5,
        labelcolor="#c9d1d9",
        framealpha=0.95,
    )
    legend.get_frame().set_linewidth(1.0)

    plt.tight_layout()
    fig.savefig(out_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    return out_path


if __name__ == "__main__":
    out = plot_gate_band()
    print(f"Saved plot to {out}")
