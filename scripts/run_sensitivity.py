#!/usr/bin/env python3
"""Sensitivity analysis on the event alignment similarity threshold.

Recomputes mean F1 for each extractor from the stored benchmark artefacts at
alignment thresholds 0.6, 0.7 (the value used in the main analysis), and 0.8.
Runs entirely post hoc; no API calls are made.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.evaluation.metrics import f1_for_input
from backend.evaluation.models import event_from_dict

THRESHOLDS = (0.6, 0.7, 0.8)

EXTRACTORS = {
    "gpt-5": ROOT / "benchmark" / "outputs",
    "claude-sonnet-4-6": ROOT / "benchmark" / "outputs_claude",
}


def main() -> int:
    results: dict = {}
    for name, output_dir in EXTRACTORS.items():
        llm_scores = {t: [] for t in THRESHOLDS}
        regex_scores = {t: [] for t in THRESHOLDS}
        for path in sorted(output_dir.glob("*.json")):
            if path.name == "summary.json":
                continue
            artefact = json.loads(path.read_text(encoding="utf-8"))
            ground_truth = [event_from_dict(e) for e in artefact["ground_truth"]]
            llm_runs = artefact.get("llm_runs") or []
            primary = [event_from_dict(e) for e in llm_runs[0]] if llm_runs else None
            regex_events = [event_from_dict(e) for e in artefact.get("regex_events", [])]
            for t in THRESHOLDS:
                if primary is not None:
                    llm_scores[t].append(f1_for_input(primary, ground_truth, t))
                regex_scores[t].append(f1_for_input(regex_events, ground_truth, t))
        results[name] = {
            "llm_mean_f1": {t: sum(v) / len(v) for t, v in llm_scores.items() if v},
            "regex_mean_f1": {t: sum(v) / len(v) for t, v in regex_scores.items() if v},
        }

    for name, r in results.items():
        print(f"\n=== {name} ===")
        for kind in ("llm_mean_f1", "regex_mean_f1"):
            row = "  ".join(f"t={t}: {v:.4f}" for t, v in r[kind].items())
            print(f"{kind:<15} {row}")

    out = ROOT / "benchmark" / "sensitivity_results.json"
    out.write_text(
        json.dumps(
            {n: {k: {str(t): v for t, v in d.items()} for k, d in r.items()} for n, r in results.items()},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
