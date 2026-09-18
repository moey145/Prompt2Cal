#!/usr/bin/env python3
"""
Generate the report's charts from the stored result artefacts.

Usage:
    python scripts/make_figures.py
    python scripts/make_figures.py --outdir report/figures

Reads:
    benchmark/verifier_results.json   (Figure 5, read directly)
    Figures 3 and 4 use the ACCURACY and OVERALL tables below; update
    them if the benchmark is re-run.

Writes:
    fig3_f1_by_category.png
    fig4_tradeoff.png
    fig5_verifier.png

Requires: matplotlib
"""

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ----------------------------------------------------------------------
# House style
# ----------------------------------------------------------------------
NAVY = "#1F4E79"
BLUE = "#2E74B5"
GREY = "#8C9BAB"
RED = "#C00000"
PINK = "#E8A0A0"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 11

CATEGORIES = ["Clean", "Typos", "Voice to text", "Ambiguous", "Missing fields"]

# Mean F1 per category, from the aggregate run summaries.
ACCURACY = {
    "Regex":             [0.095, 0.000, 0.000, 0.030, 0.000],
    "GPT-5":             [0.779, 0.709, 0.714, 0.610, 0.583],
    "Claude Sonnet 4.6": [0.829, 0.759, 0.780, 0.654, 0.759],
}

# Overall mean F1 and hallucination rate on the missing-fields subset.
OVERALL = {
    "Regex":             {"f1": 0.025, "hallucination": 0.000, "colour": GREY},
    "GPT-5":             {"f1": 0.679, "hallucination": 0.517, "colour": BLUE},
    "Claude Sonnet 4.6": {"f1": 0.756, "hallucination": 0.646, "colour": NAVY},
}


def tidy(ax):
    """Strip chart junk: no top or right spine, dashed grid behind the bars."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)


def label_bars(ax, bars, fmt="{:.2f}", threshold=0.005):
    for bar in bars:
        h = bar.get_height()
        if h > threshold:
            ax.annotate(fmt.format(h),
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 2), textcoords="offset points",
                        ha="center", fontsize=8)


# ----------------------------------------------------------------------
# Figure 3: mean F1 by input category
# ----------------------------------------------------------------------
def figure_f1_by_category(outdir):
    x = np.arange(len(CATEGORIES))
    width = 0.26
    colours = {"Regex": GREY, "GPT-5": BLUE, "Claude Sonnet 4.6": NAVY}

    fig, ax = plt.subplots(figsize=(9, 4.6))
    for offset, (name, values) in zip((-width, 0, width), ACCURACY.items()):
        bars = ax.bar(x + offset, values, width, label=name, color=colours[name])
        label_bars(ax, bars)

    ax.set_ylabel("Mean F1 score")
    ax.set_xlabel("Input category")
    ax.set_title("Mean field-level F1 by input category and extractor")
    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORIES)
    ax.set_ylim(0, 1.0)
    ax.legend(frameon=False)
    tidy(ax)

    path = os.path.join(outdir, "fig3_f1_by_category.png")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


# ----------------------------------------------------------------------
# Figure 4: accuracy versus faithfulness trade-off
# ----------------------------------------------------------------------
def figure_tradeoff(outdir):
    fig, ax = plt.subplots(figsize=(8, 5))

    for name, d in OVERALL.items():
        ax.scatter(d["f1"], d["hallucination"], s=260, color=d["colour"],
                   zorder=3, edgecolors="white", linewidths=1.5)
        # Place GPT-5 and Claude labels to the left of the point; Regex to the right.
        left = name in ("GPT-5", "Claude Sonnet 4.6")
        ax.annotate(name, xy=(d["f1"], d["hallucination"]),
                    xytext=(-12, 8) if left else (12, 8),
                    textcoords="offset points", fontsize=11,
                    ha="right" if left else "left")

    ax.set_xlabel("Mean F1 (accuracy, all 100 inputs)")
    ax.set_ylabel("Hallucination rate (missing fields subset)")
    ax.set_title("The accuracy versus faithfulness trade-off")
    ax.set_xlim(-0.05, 0.9)
    ax.set_ylim(-0.05, 0.8)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = os.path.join(outdir, "fig4_tradeoff.png")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


# ----------------------------------------------------------------------
# Figure 5: verifier recall against usability cost
# ----------------------------------------------------------------------
def figure_verifier(outdir, results):
    models = [("gpt-5", "GPT-5"), ("claude-sonnet-4-6", "Claude Sonnet 4.6")]
    labels = [display for _, display in models]

    def pct(key, scope, field):
        return results[key]["scopes"][scope][field] * 100

    missing_recall = [pct(k, "missing_fields", "detection_recall") for k, _ in models]
    full_recall = [pct(k, "all", "detection_recall") for k, _ in models]
    full_ff = [pct(k, "all", "false_flag_rate") for k, _ in models]
    clean_ff = [pct(k, "clean", "false_flag_rate") for k, _ in models]

    x = np.arange(len(models))
    width = 0.32

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))

    panels = [
        (ax1, missing_recall, full_recall, "Missing fields subset", "Full dataset",
         NAVY, GREY, "Detection recall (%)", "Fabrications caught by the verifier"),
        (ax2, full_ff, clean_ff, "Full dataset", "Clean subset",
         RED, PINK, "False flag rate (%)", "Usability cost: legitimate fields flagged"),
    ]

    for ax, a_vals, b_vals, a_label, b_label, a_col, b_col, ylabel, title in panels:
        bars_a = ax.bar(x - width / 2, a_vals, width, label=a_label, color=a_col)
        bars_b = ax.bar(x + width / 2, b_vals, width, label=b_label, color=b_col)
        for bars in (bars_a, bars_b):
            label_bars(ax, bars, fmt="{:.1f}%", threshold=-1)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 105)          # shared scale so the panels are comparable
        ax.legend(frameon=False, fontsize=9)
        tidy(ax)

    path = os.path.join(outdir, "fig5_verifier.png")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description="Generate report charts.")
    parser.add_argument("--outdir", default="report/figures",
                        help="directory to write PNGs into")
    parser.add_argument("--results", default="benchmark/verifier_results.json",
                        help="path to verifier_results.json")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    with open(args.results) as fh:
        verifier = json.load(fh)

    for path in (figure_f1_by_category(args.outdir),
                 figure_tradeoff(args.outdir),
                 figure_verifier(args.outdir, verifier)):
        print("wrote", path)


if __name__ == "__main__":
    main()
