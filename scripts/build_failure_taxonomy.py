#!/usr/bin/env python3
"""Build a failure-mode taxonomy from the stored benchmark artefacts.

Categorises every deviation from ground truth for each extractor's primary
run into one of seven failure modes. Runs post hoc; no API calls.

Event-level modes:
  empty_output    prediction list empty while ground truth is non-empty
  missed_event    a ground-truth event has no aligned prediction
  spurious_event  a predicted event has no aligned ground-truth event

Field-level modes (within aligned event pairs):
  fabricated_field  ground truth null, prediction non-null (hallucination)
  missed_field      ground truth non-null, prediction null
  wrong_time        start_time or end_time both non-null but mismatched
  wrong_other       any other field both non-null but mismatched
                    (title, location, notes, recurrence_type)

Counts are occurrences (not inputs), except empty_output which is per input.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.evaluation.alignment import align_events
from backend.evaluation.models import EVAL_FIELDS, event_from_dict
from backend.evaluation.normalize import field_matches

TIME_FIELDS = ("start_time", "end_time")

EXTRACTORS = {
    "gpt-5": (ROOT / "benchmark" / "outputs", "llm"),
    "claude-sonnet-4-6": (ROOT / "benchmark" / "outputs_claude", "llm"),
    "regex": (ROOT / "benchmark" / "outputs", "regex"),
}


def _is_null(field_name: str, value) -> bool:
    if field_name == "recurrence_type":
        return value in (None, "", "none")
    return value in (None, "")


def categorise(predicted, ground_truth, counts: Counter) -> None:
    if not predicted and ground_truth:
        counts["empty_output"] += 1
        return
    pairs, spurious, missed = align_events(predicted, ground_truth)
    counts["missed_event"] += len(missed)
    counts["spurious_event"] += len(spurious)
    for pred_event, gt_event in pairs:
        pred_dict = pred_event.to_dict()
        gt_dict = gt_event.to_dict()
        for field_name in EVAL_FIELDS:
            pred_value = pred_dict.get(field_name)
            gt_value = gt_dict.get(field_name)
            pred_null = _is_null(field_name, pred_value)
            gt_null = _is_null(field_name, gt_value)
            if pred_null and gt_null:
                continue
            if gt_null and not pred_null:
                counts["fabricated_field"] += 1
            elif pred_null and not gt_null:
                counts["missed_field"] += 1
            elif not field_matches(pred_value, gt_value):
                if field_name in TIME_FIELDS:
                    counts["wrong_time"] += 1
                else:
                    counts["wrong_other"] += 1


def main() -> int:
    results = {}
    for name, (output_dir, kind) in EXTRACTORS.items():
        counts: Counter = Counter()
        for path in sorted(output_dir.glob("*.json")):
            if path.name == "summary.json":
                continue
            artefact = json.loads(path.read_text(encoding="utf-8"))
            ground_truth = [event_from_dict(e) for e in artefact["ground_truth"]]
            if kind == "llm":
                runs = artefact.get("llm_runs") or []
                predicted = [event_from_dict(e) for e in runs[0]] if runs else []
            else:
                predicted = [event_from_dict(e) for e in artefact.get("regex_events", [])]
            categorise(predicted, ground_truth, counts)
        results[name] = dict(counts)

    modes = [
        "empty_output",
        "missed_event",
        "spurious_event",
        "fabricated_field",
        "missed_field",
        "wrong_time",
        "wrong_other",
    ]
    header = f"{'mode':<18}" + "".join(f"{n:>20}" for n in results)
    print(header)
    for mode in modes:
        print(f"{mode:<18}" + "".join(f"{results[n].get(mode, 0):>20}" for n in results))

    out = ROOT / "benchmark" / "failure_taxonomy.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
