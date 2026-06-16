#!/usr/bin/env python3
"""Run the Prompt2Cal research evaluation harness."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.evaluation.models import load_dataset
from backend.evaluation.runner import EvaluationRunner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LLM vs Regex benchmark evaluation.")
    parser.add_argument(
        "--dataset",
        default=str(ROOT / "benchmark" / "dataset.json"),
        help="Path to benchmark dataset JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "benchmark" / "outputs"),
        help="Directory for per-input outputs and summary.json.",
    )
    parser.add_argument(
        "--input-id",
        action="append",
        dest="input_ids",
        help="Run only specific input IDs. Can be passed multiple times.",
    )
    parser.add_argument(
        "--llm-runs",
        type=int,
        default=3,
        help="Number of repeated LLM runs per input for consistency measurement.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="LLM temperature for evaluation runs.",
    )
    parser.add_argument(
        "--regex-only",
        action="store_true",
        help="Run only the Regex extractor (no OpenAI API calls).",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    dataset = load_dataset(args.dataset)
    runner = EvaluationRunner(
        dataset=dataset,
        output_dir=args.output_dir,
        llm_runs=args.llm_runs,
        llm_temperature=args.temperature,
        regex_only=args.regex_only,
    )
    payload = await runner.run(input_ids=args.input_ids)
    print(json.dumps(payload["summary"], indent=2))
    print(f"\nWrote results to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
