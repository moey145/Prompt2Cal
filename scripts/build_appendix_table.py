#!/usr/bin/env python3
"""Generate appendix tables (Markdown + LaTeX longtable) of the benchmark dataset.

Reads benchmark/dataset.json and writes:
  - benchmark/APPENDIX_dataset.md
  - benchmark/APPENDIX_dataset.tex
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "benchmark" / "dataset.json"
MD_OUT = ROOT / "benchmark" / "APPENDIX_dataset.md"
TEX_OUT = ROOT / "benchmark" / "APPENDIX_dataset.tex"

CATEGORY_LABELS = {
    "clean": "Clean",
    "typos": "Typos",
    "voice_to_text": "Voice-to-text",
    "ambiguous": "Ambiguous",
    "missing_fields": "Missing fields",
}


def summarize_ground_truth(events: list[dict]) -> str:
    """Compact one-line summary of the ground-truth events for an input."""
    parts = []
    for event in events:
        title = event.get("title") or "(none)"
        start = event.get("start_time")
        start_str = start if start else "null"
        segment = f"{title} @ {start_str}"

        extras = []
        if event.get("end_time"):
            extras.append(f"end: {event['end_time']}")
        if event.get("location"):
            extras.append(f"loc: {event['location']}")
        rec = event.get("recurrence_type")
        if rec and rec != "none":
            extras.append(f"recur: {rec}")
        if extras:
            segment += " (" + ", ".join(extras) + ")"
        parts.append(segment)
    return "; ".join(parts)


def escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def build_markdown(inputs: list[dict]) -> str:
    lines = [
        "# Appendix A: Benchmark dataset (100 inputs)",
        "",
        "Stratified benchmark of 100 natural-language inputs (20 per category) "
        "with ground-truth event labels. Times are relative to the "
        "Australia/Sydney timezone.",
        "",
        "| ID | Category | Input text | Ground-truth events |",
        "| --- | --- | --- | --- |",
    ]
    for item in inputs:
        cat = CATEGORY_LABELS.get(item["category"], item["category"])
        text = item["text"].replace("|", "\\|")
        gt = summarize_ground_truth(item["ground_truth"]).replace("|", "\\|")
        lines.append(f"| {item['id']} | {cat} | {text} | {gt} |")
    lines.append("")
    return "\n".join(lines)


def build_latex(inputs: list[dict]) -> str:
    header = r"""% Appendix A: Benchmark dataset (requires \usepackage{longtable})
\begin{longtable}{@{}p{2.2cm}p{2.1cm}p{5cm}p{5cm}@{}}
\caption{Benchmark dataset of 100 inputs with ground-truth event labels.}
\label{tab:appendix-dataset}\\
\toprule
\textbf{ID} & \textbf{Category} & \textbf{Input text} & \textbf{Ground-truth events} \\
\midrule
\endfirsthead
\multicolumn{4}{c}{{\tablename\ \thetable{} (continued from previous page)}}\\
\toprule
\textbf{ID} & \textbf{Category} & \textbf{Input text} & \textbf{Ground-truth events} \\
\midrule
\endhead
\midrule
\multicolumn{4}{r}{{Continued on next page}}\\
\endfoot
\bottomrule
\endlastfoot
"""
    rows = []
    for item in inputs:
        cat = CATEGORY_LABELS.get(item["category"], item["category"])
        row = " & ".join(
            [
                escape_latex(item["id"]),
                escape_latex(cat),
                escape_latex(item["text"]),
                escape_latex(summarize_ground_truth(item["ground_truth"])),
            ]
        )
        rows.append(row + r" \\")
    footer = "\n\\end{longtable}\n"
    return header + "\n".join(rows) + footer


def main() -> int:
    data = json.load(open(DATASET, encoding="utf-8"))
    inputs = data["inputs"]

    MD_OUT.write_text(build_markdown(inputs), encoding="utf-8")
    TEX_OUT.write_text(build_latex(inputs), encoding="utf-8")

    print(f"Wrote {len(inputs)} rows to:")
    print(f"  {MD_OUT}")
    print(f"  {TEX_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
