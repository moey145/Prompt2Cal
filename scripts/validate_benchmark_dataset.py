#!/usr/bin/env python3
"""Validate benchmark dataset structure against the research design."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.evaluation.models import CATEGORIES, EVAL_FIELDS, load_dataset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate benchmark dataset JSON.")
    parser.add_argument(
        "--dataset",
        default=str(ROOT / "benchmark" / "dataset.json"),
        help="Path to benchmark dataset JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset = load_dataset(args.dataset)
    errors: list[str] = []

    counts = Counter(item.category for item in dataset.inputs)
    for category in CATEGORIES:
        if counts.get(category, 0) != 20:
            errors.append(f"Category '{category}' has {counts.get(category, 0)} inputs (expected 20).")

    ids = [item.id for item in dataset.inputs]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate input IDs found.")

    for item in dataset.inputs:
        if not item.text.strip():
            errors.append(f"{item.id}: empty input text.")
        if not item.ground_truth:
            errors.append(f"{item.id}: missing ground_truth events.")
        for event_index, event in enumerate(item.ground_truth):
            payload = event.to_dict()
            for field_name in EVAL_FIELDS:
                if field_name not in payload:
                    errors.append(f"{item.id} event {event_index}: missing field '{field_name}'.")

    if errors:
        print("Dataset validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"Dataset valid: {len(dataset.inputs)} inputs across {len(CATEGORIES)} categories.")
    for category in CATEGORIES:
        print(f"  {category}: {counts[category]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
