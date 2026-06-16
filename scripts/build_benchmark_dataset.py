#!/usr/bin/env python3
"""Build benchmark/dataset.json from the curated inputs catalog."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark.inputs_catalog import all_inputs  # noqa: E402


def main() -> int:
    dataset = {
        "version": "1.0",
        "timezone": "Australia/Sydney",
        "inputs": all_inputs(),
    }
    output_path = ROOT / "benchmark" / "dataset.json"
    output_path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(dataset['inputs'])} inputs to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
