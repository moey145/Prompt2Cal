from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

EVAL_FIELDS = (
    "title",
    "start_time",
    "end_time",
    "location",
    "notes",
    "recurrence_type",
)

CATEGORIES = (
    "clean",
    "typos",
    "voice_to_text",
    "ambiguous",
    "missing_fields",
)


@dataclass
class EvalEvent:
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    recurrence_type: Optional[str] = "none"

    def to_dict(self) -> Dict[str, Any]:
        return {name: getattr(self, name) for name in EVAL_FIELDS}


@dataclass
class BenchmarkInput:
    id: str
    category: str
    text: str
    ground_truth: List[EvalEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "text": self.text,
            "ground_truth": [event.to_dict() for event in self.ground_truth],
        }


@dataclass
class BenchmarkDataset:
    version: str
    timezone: str
    inputs: List[BenchmarkInput] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "timezone": self.timezone,
            "inputs": [item.to_dict() for item in self.inputs],
        }


def event_from_dict(data: Dict[str, Any]) -> EvalEvent:
    return EvalEvent(
        title=data.get("title"),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        location=data.get("location"),
        notes=data.get("notes"),
        recurrence_type=data.get("recurrence_type") or "none",
    )


def load_dataset(path: str) -> BenchmarkDataset:
    import json

    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)

    inputs = []
    for item in payload.get("inputs", []):
        inputs.append(
            BenchmarkInput(
                id=item["id"],
                category=item["category"],
                text=item["text"],
                ground_truth=[event_from_dict(event) for event in item.get("ground_truth", [])],
            )
        )

    return BenchmarkDataset(
        version=payload.get("version", "1.0"),
        timezone=payload.get("timezone", "UTC"),
        inputs=inputs,
    )


def save_dataset(dataset: BenchmarkDataset, path: str) -> None:
    import json

    with open(path, "w", encoding="utf-8") as handle:
        json.dump(dataset.to_dict(), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
