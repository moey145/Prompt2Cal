#!/usr/bin/env python3
"""Compare re-run outputs against the original benchmark outputs.

Checks:
1. Regex determinism: per-input regex events from the regex-only re-run must
   be byte-identical to the original run.
2. Claude run-to-run stability: headline summary metrics from the Claude
   re-run compared to the original Claude run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_regex(original_dir: Path, rerun_dir: Path) -> None:
    mismatches = []
    count = 0
    for path in sorted(original_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        rerun_path = rerun_dir / path.name
        if not rerun_path.exists():
            mismatches.append(f"{path.name}: missing in re-run")
            continue
        original = load(path)["regex_events"]
        rerun = load(rerun_path)["regex_events"]
        count += 1
        if original != rerun:
            mismatches.append(path.name)
    print(f"Regex determinism: {count} inputs compared, {len(mismatches)} mismatches")
    for m in mismatches:
        print(f"  MISMATCH: {m}")


def check_claude(original_summary: Path, rerun_summary: Path) -> None:
    orig = load(original_summary)["summary"]
    rerun = load(rerun_summary)["summary"]
    rows = [
        ("llm_mean_f1", orig["accuracy"]["llm_mean_f1"], rerun["accuracy"]["llm_mean_f1"]),
        ("llm_robustness_drop", orig["robustness"]["llm_drop"], rerun["robustness"]["llm_drop"]),
        (
            "llm_consistency",
            orig["consistency"]["llm_pairwise_agreement_mean"],
            rerun["consistency"]["llm_pairwise_agreement_mean"],
        ),
        (
            "llm_hallucination",
            orig["hallucination"]["llm_rate_mean"],
            rerun["hallucination"]["llm_rate_mean"],
        ),
    ]
    print("\nClaude run-to-run stability (original vs re-run):")
    for name, a, b in rows:
        print(f"  {name:<22} {a:.4f}  vs  {b:.4f}   delta={abs(a - b):.4f}")
    print("\nCategory mean F1 (original vs re-run):")
    for cat, (a, _) in orig["statistics"]["category_mean_f1"].items():
        b = rerun["statistics"]["category_mean_f1"][cat][0]
        print(f"  {cat:<16} {a:.4f}  vs  {b:.4f}   delta={abs(a - b):.4f}")


if __name__ == "__main__":
    check_regex(ROOT / "benchmark" / "outputs", ROOT / "benchmark" / "outputs_regex_rerun")
    claude_rerun = ROOT / "benchmark" / "outputs_claude_rerun" / "summary.json"
    if claude_rerun.exists():
        check_claude(ROOT / "benchmark" / "outputs_claude" / "summary.json", claude_rerun)
    else:
        print("\nClaude re-run summary not present yet.")
    sys.exit(0)
