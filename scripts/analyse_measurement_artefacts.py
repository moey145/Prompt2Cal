#!/usr/bin/env python3
"""Measurement artefacts in the consistency and hallucination metrics.

Two post hoc checks over the stored benchmark artefacts; no API calls are made.

1. Consistency to the minute. When a model answers "now" (as Appendix B.2,
   instruction 9 asks when no time is given), each run resolves it to the clock
   time of its own API call, seconds apart, so identical model answers score as
   disagreements. This recomputes pairwise consistency with start and end times
   truncated to the minute, alongside the reported value.

2. Where the fabricated fields on the missing-fields subset came from. Each
   fabrication counted by the hallucination metric (all LLM runs) is assigned to
   one source:
     unmatched_event_fields  fields of a predicted event that failed title
                             alignment (every non-null field counts)
     default_end_time        end time exactly start + 60 minutes, the pipeline
                             default from duration_minutes
     clock_filled_start      start time with non-zero seconds, i.e. a clock time
                             filled from the current time, not chosen by the model
     model_chosen_start      start time on a whole minute, chosen by the model
     other_end_time, notes, location, recurrence_type, title

Writes benchmark/measurement_artefacts.json.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.evaluation.alignment import align_events
from backend.evaluation.metrics import events_equal
from backend.evaluation.models import EVAL_FIELDS, event_from_dict

EXTRACTORS = {
    "gpt-5": ROOT / "benchmark" / "outputs",
    "claude-sonnet-4-6": ROOT / "benchmark" / "outputs_claude",
}
DEFAULT_DURATION_SECONDS = 3600


def load_artefacts(output_dir: Path):
    for path in sorted(output_dir.glob("*.json")):
        if path.name != "summary.json":
            yield json.loads(path.read_text(encoding="utf-8"))


def to_minute(event_dict: dict) -> dict:
    out = dict(event_dict)
    for key in ("start_time", "end_time"):
        if out.get(key):
            out[key] = datetime.fromisoformat(out[key]).replace(second=0, microsecond=0).isoformat()
    return out


def pairwise(runs) -> float:
    pairs = list(combinations(runs, 2))
    if not pairs:
        return 1.0
    return sum(1.0 if events_equal(a, b) else 0.0 for a, b in pairs) / len(pairs)


def mean(values) -> float:
    return sum(values) / len(values) if values else 0.0


def consistency(artefacts) -> dict:
    reported, by_minute = {}, {}
    for artefact in artefacts:
        runs = artefact.get("llm_runs") or []
        raw = [[event_from_dict(e) for e in run] for run in runs]
        truncated = [[event_from_dict(to_minute(e)) for e in run] for run in runs]
        reported.setdefault(artefact["category"], []).append(pairwise(raw))
        by_minute.setdefault(artefact["category"], []).append(pairwise(truncated))

    def summarise(scores):
        return {
            "overall": round(mean([s for v in scores.values() for s in v]), 3),
            "by_category": {c: round(mean(v), 3) for c, v in sorted(scores.items())},
        }

    return {"reported": summarise(reported), "to_the_minute": summarise(by_minute)}


def classify(field_name: str, predicted: dict) -> str:
    if field_name == "start_time":
        t = datetime.fromisoformat(predicted["start_time"])
        return "clock_filled_start" if (t.second or t.microsecond) else "model_chosen_start"
    if field_name == "end_time":
        if predicted.get("start_time"):
            gap = datetime.fromisoformat(predicted["end_time"]) - datetime.fromisoformat(predicted["start_time"])
            if abs(gap.total_seconds() - DEFAULT_DURATION_SECONDS) < 5:
                return "default_end_time"
        return "other_end_time"
    return field_name


def fabrication_sources(artefacts) -> dict:
    sources: Counter = Counter()
    opportunities = 0
    for artefact in artefacts:
        if artefact["category"] != "missing_fields":
            continue
        ground_truth = [event_from_dict(e) for e in artefact["ground_truth"]]
        for run in artefact.get("llm_runs") or []:
            predicted = [event_from_dict(e) for e in run]
            pairs, unmatched, _ = align_events(predicted, ground_truth)
            for pred, gt in pairs:
                pred_dict, gt_dict = pred.to_dict(), gt.to_dict()
                for field_name in EVAL_FIELDS:
                    if gt_dict[field_name] is None:
                        opportunities += 1
                        if pred_dict[field_name] is not None:
                            sources[classify(field_name, pred_dict)] += 1
            for pred in unmatched:
                opportunities += len(EVAL_FIELDS)
                sources["unmatched_event_fields"] += sum(v is not None for v in pred.to_dict().values())
    total = sum(sources.values())
    return {
        "opportunities": opportunities,
        "fabrications": total,
        "sources": {
            name: {"count": count, "share": round(count / total, 3)}
            for name, count in sources.most_common()
        },
    }


def main() -> int:
    results = {}
    for name, output_dir in EXTRACTORS.items():
        artefacts = list(load_artefacts(output_dir))
        results[name] = {
            "consistency": consistency(artefacts),
            "missing_fields_fabrication_sources": fabrication_sources(artefacts),
        }

    out_path = ROOT / "benchmark" / "measurement_artefacts.json"
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    for name, r in results.items():
        c = r["consistency"]
        print(f"{name}: consistency {c['reported']['overall']} reported, "
              f"{c['to_the_minute']['overall']} to the minute")
        for cat, value in c["to_the_minute"]["by_category"].items():
            print(f"    {cat:15s} {c['reported']['by_category'][cat]:.3f} -> {value:.3f}")
        f = r["missing_fields_fabrication_sources"]
        print(f"  missing-fields fabrications: {f['fabrications']} of {f['opportunities']} opportunities")
        for source, s in f["sources"].items():
            print(f"    {s['count']:4d}  {s['share']:6.1%}  {source}")
    print(f"wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
