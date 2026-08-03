#!/usr/bin/env python3
"""Score the source-grounding verifier against existing benchmark artefacts.

Runs entirely post-hoc over the per-input JSON artefacts produced by
scripts/run_evaluation.py; no API calls are made.

For each input, the primary LLM run (the same run used by the hallucination
metric) is aligned to ground truth and every non-null predicted field is
classified two ways:

  actual:    fabricated  (ground truth field is null, prediction is non-null)
             legitimate  (ground truth field is non-null)
  predicted: flagged     (verifier says ungrounded)
             not flagged (verifier says grounded)

Confusion matrix per extractor:
  TP fabricated and flagged (caught)
  FN fabricated and not flagged (missed)
  FP legitimate and flagged (false alarm, the usability cost)
  TN legitimate and not flagged

Fields in unaligned predicted events (no matching ground-truth event) count
as fabricated, consistent with the hallucination metric. Recurrence "none"
is abstention and is excluded, also consistent with the hallucination metric.

Outputs headline detection numbers on the missing-fields subset, the false
flag rate over the full dataset and the clean subset, and writes
benchmark/verifier_results.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.evaluation.alignment import align_events
from backend.evaluation.models import EVAL_FIELDS, event_from_dict
from backend.evaluation.verifier import UNGROUNDED, verify_event


def _is_null(field_name: str, value) -> bool:
    if field_name == "recurrence_type":
        return value in (None, "", "none")
    return value in (None, "")


def _new_matrix() -> dict:
    return {"tp": 0, "fn": 0, "fp": 0, "tn": 0}


def score_artefact(artefact: dict, matrices: dict) -> None:
    source = artefact["text"]
    category = artefact["category"]
    llm_runs = artefact.get("llm_runs") or []
    if not llm_runs:
        return
    primary = [event_from_dict(e) for e in llm_runs[0]]
    ground_truth = [event_from_dict(e) for e in artefact.get("ground_truth", [])]

    pairs, false_positive_events, _ = align_events(primary, ground_truth)

    def tally(pred_dict: dict, gt_dict: dict | None) -> None:
        flags = verify_event(pred_dict, source)
        for field_name in EVAL_FIELDS:
            pred_value = pred_dict.get(field_name)
            if _is_null(field_name, pred_value):
                continue  # abstention is never scored
            fabricated = gt_dict is None or gt_dict.get(field_name) is None
            flagged = flags[field_name] == UNGROUNDED
            for scope in ("all", category):
                m = matrices[scope]
                if fabricated and flagged:
                    m["tp"] += 1
                elif fabricated and not flagged:
                    m["fn"] += 1
                elif not fabricated and flagged:
                    m["fp"] += 1
                else:
                    m["tn"] += 1

    for pred_event, gt_event in pairs:
        tally(pred_event.to_dict(), gt_event.to_dict())
    for pred_event in false_positive_events:
        tally(pred_event.to_dict(), None)


def summarise(matrix: dict) -> dict:
    tp, fn, fp, tn = matrix["tp"], matrix["fn"], matrix["fp"], matrix["tn"]
    fabricated = tp + fn
    legitimate = fp + tn
    recall = tp / fabricated if fabricated else None
    precision = tp / (tp + fp) if (tp + fp) else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision and recall and (precision + recall)
        else None
    )
    false_flag_rate = fp / legitimate if legitimate else None
    return {
        **matrix,
        "fabricated_fields": fabricated,
        "legitimate_fields": legitimate,
        "detection_recall": recall,
        "detection_precision": precision,
        "detection_f1": f1,
        "false_flag_rate": false_flag_rate,
    }


def score_extractor(output_dir: Path) -> dict:
    matrices: dict = defaultdict(_new_matrix)
    count = 0
    for path in sorted(output_dir.glob("*.json")):
        if path.name == "summary.json":
            continue
        artefact = json.loads(path.read_text(encoding="utf-8"))
        score_artefact(artefact, matrices)
        count += 1
    return {
        "inputs_scored": count,
        "scopes": {scope: summarise(matrix) for scope, matrix in matrices.items()},
    }


def _fmt(value) -> str:
    return f"{value:.3f}" if isinstance(value, float) else "n/a"


def main() -> int:
    parser = argparse.ArgumentParser(description="Score the source-grounding verifier.")
    parser.add_argument(
        "--extractor",
        action="append",
        nargs=2,
        metavar=("NAME", "OUTPUT_DIR"),
        dest="extractors",
        help="Extractor name and artefact directory. Repeatable.",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "benchmark" / "verifier_results.json"),
        help="Path for the JSON results file.",
    )
    args = parser.parse_args()

    extractors = args.extractors or [
        ["gpt-5", str(ROOT / "benchmark" / "outputs")],
        ["claude-sonnet-4-6", str(ROOT / "benchmark" / "outputs_claude")],
    ]

    results = {}
    for name, output_dir in extractors:
        results[name] = score_extractor(Path(output_dir))

    for name, result in results.items():
        print(f"\n=== {name} ({result['inputs_scored']} inputs) ===")
        missing = result["scopes"].get("missing_fields", {})
        overall = result["scopes"].get("all", {})
        clean = result["scopes"].get("clean", {})
        print(
            f"missing_fields: fabricated={missing.get('fabricated_fields')} "
            f"caught={missing.get('tp')} recall={_fmt(missing.get('detection_recall'))} "
            f"precision={_fmt(missing.get('detection_precision'))} "
            f"f1={_fmt(missing.get('detection_f1'))}"
        )
        print(
            f"overall:        fabricated={overall.get('fabricated_fields')} "
            f"caught={overall.get('tp')} recall={_fmt(overall.get('detection_recall'))} "
            f"false_flag_rate={_fmt(overall.get('false_flag_rate'))} "
            f"(legitimate={overall.get('legitimate_fields')})"
        )
        print(
            f"clean subset:   false_flag_rate={_fmt(clean.get('false_flag_rate'))} "
            f"(legitimate={clean.get('legitimate_fields')})"
        )

    output_path = Path(args.output)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote verifier results to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
