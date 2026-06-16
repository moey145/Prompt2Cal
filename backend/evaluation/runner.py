from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .extractors import LLMExtractor, RegexExtractor
from .metrics import (
    f1_for_input,
    hallucination_rate,
    input_is_fully_correct,
    mcnemar_test,
    pairwise_consistency,
    robustness_drop,
    wilcoxon_category_test,
)
from .models import BenchmarkDataset, BenchmarkInput, EvalEvent, load_dataset
from .normalize import normalize_event_list


@dataclass
class InputRunResult:
    input_id: str
    category: str
    text: str
    regex_events: List[Dict[str, Any]]
    llm_runs: List[List[Dict[str, Any]]]
    ground_truth: List[Dict[str, Any]]
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationSummary:
    accuracy: Dict[str, float]
    robustness: Dict[str, float]
    consistency: Dict[str, float]
    hallucination: Dict[str, float]
    statistics: Dict[str, Any] = field(default_factory=dict)


class EvaluationRunner:
    def __init__(
        self,
        dataset: BenchmarkDataset,
        output_dir: str | Path,
        llm_runs: int = 3,
        llm_temperature: float = 0.0,
        regex_only: bool = False,
    ):
        self.dataset = dataset
        self.output_dir = Path(output_dir)
        self.llm_runs = llm_runs
        self.llm_temperature = llm_temperature
        self.regex_only = regex_only
        self.regex_extractor = RegexExtractor()
        self.llm_extractor = None if regex_only else LLMExtractor()

    async def run(self, input_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        selected_inputs = self._select_inputs(input_ids)
        results: List[InputRunResult] = []

        for benchmark_input in selected_inputs:
            result = await self._run_input(benchmark_input)
            results.append(result)
            self._write_input_result(result)

        summary = self._summarize(results)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_version": self.dataset.version,
            "timezone": self.dataset.timezone,
            "llm_runs": self.llm_runs,
            "llm_temperature": self.llm_temperature,
            "regex_only": self.regex_only,
            "results": [self._result_to_dict(result) for result in results],
            "summary": self._summary_to_dict(summary),
        }
        summary_path = self.output_dir / "summary.json"
        summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def _select_inputs(self, input_ids: Optional[List[str]]) -> List[BenchmarkInput]:
        if not input_ids:
            return self.dataset.inputs
        selected = {item.id: item for item in self.dataset.inputs}
        return [selected[item_id] for item_id in input_ids if item_id in selected]

    async def _run_input(self, benchmark_input: BenchmarkInput) -> InputRunResult:
        timezone_name = self.dataset.timezone
        ground_truth = normalize_event_list(benchmark_input.ground_truth, timezone_name)
        regex_events = self.regex_extractor.extract(benchmark_input.text, timezone_name)

        llm_runs: List[List[EvalEvent]] = []
        if not self.regex_only:
            for _ in range(self.llm_runs):
                llm_events = await self.llm_extractor.extract(
                    benchmark_input.text,
                    timezone_name,
                    use_cache=False,
                    temperature=self.llm_temperature,
                )
                llm_runs.append(llm_events)

        metrics = self._compute_input_metrics(
            regex_events=regex_events,
            llm_runs=llm_runs,
            ground_truth=ground_truth,
            category=benchmark_input.category,
            timezone_name=timezone_name,
        )

        return InputRunResult(
            input_id=benchmark_input.id,
            category=benchmark_input.category,
            text=benchmark_input.text,
            regex_events=[event.to_dict() for event in regex_events],
            llm_runs=[[event.to_dict() for event in run] for run in llm_runs],
            ground_truth=[event.to_dict() for event in ground_truth],
            metrics=metrics,
        )

    def _write_input_result(self, result: InputRunResult) -> None:
        path = self.output_dir / f"{result.input_id}.json"
        path.write_text(json.dumps(self._result_to_dict(result), indent=2), encoding="utf-8")

    def _result_to_dict(self, result: InputRunResult) -> Dict[str, Any]:
        return {
            "input_id": result.input_id,
            "category": result.category,
            "text": result.text,
            "regex_events": result.regex_events,
            "llm_runs": result.llm_runs,
            "ground_truth": result.ground_truth,
            "metrics": result.metrics,
        }

    def _compute_input_metrics(
        self,
        *,
        regex_events: List[EvalEvent],
        llm_runs: List[List[EvalEvent]],
        ground_truth: List[EvalEvent],
        category: str,
        timezone_name: str,
    ) -> Dict[str, Any]:
        regex_f1 = f1_for_input(regex_events, ground_truth)
        regex_correct = input_is_fully_correct(regex_events, ground_truth)
        metrics: Dict[str, Any] = {
            "regex_f1": regex_f1,
            "regex_fully_correct": regex_correct,
        }

        if category == "missing_fields":
            regex_h = hallucination_rate(regex_events, ground_truth)
            if regex_h is not None:
                metrics["regex_hallucination_rate"] = regex_h

        if llm_runs:
            primary_llm = llm_runs[0]
            metrics["llm_f1"] = f1_for_input(primary_llm, ground_truth)
            metrics["llm_fully_correct"] = input_is_fully_correct(primary_llm, ground_truth)
            metrics["llm_pairwise_consistency"] = pairwise_consistency(llm_runs)
            if category == "missing_fields":
                llm_h = hallucination_rate(primary_llm, ground_truth)
                if llm_h is not None:
                    metrics["llm_hallucination_rate"] = llm_h

        return metrics

    def _summarize(self, results: List[InputRunResult]) -> EvaluationSummary:
        timezone_name = self.dataset.timezone
        llm_f1_values: List[float] = []
        regex_f1_values: List[float] = []
        llm_correct: List[bool] = []
        regex_correct: List[bool] = []
        consistency_values: List[float] = []
        hallucination_llm: List[float] = []
        hallucination_regex: List[float] = []
        category_scores: Dict[str, Dict[str, List[float]]] = {}

        for result in results:
            ground_truth = normalize_event_list(
                [EvalEvent(**event) for event in result.ground_truth],
                timezone_name,
            )
            regex_events = normalize_event_list(
                [EvalEvent(**event) for event in result.regex_events],
                timezone_name,
            )
            llm_runs = [
                normalize_event_list([EvalEvent(**event) for event in run], timezone_name)
                for run in result.llm_runs
            ]
            primary_llm = llm_runs[0] if llm_runs else []

            regex_f1 = f1_for_input(regex_events, ground_truth)
            regex_f1_values.append(regex_f1)
            regex_correct.append(input_is_fully_correct(regex_events, ground_truth))

            category_scores.setdefault(result.category, {"llm": [], "regex": []})
            category_scores[result.category]["regex"].append(regex_f1)

            if llm_runs:
                llm_f1 = f1_for_input(primary_llm, ground_truth)
                llm_f1_values.append(llm_f1)
                llm_correct.append(input_is_fully_correct(primary_llm, ground_truth))
                category_scores[result.category]["llm"].append(llm_f1)
                consistency_values.append(pairwise_consistency(llm_runs))

            if result.category == "missing_fields":
                if llm_runs:
                    llm_h = hallucination_rate(primary_llm, ground_truth)
                    if llm_h is not None:
                        hallucination_llm.append(llm_h)
                regex_h = hallucination_rate(regex_events, ground_truth)
                if regex_h is not None:
                    hallucination_regex.append(regex_h)

        clean_llm = _mean(category_scores.get("clean", {}).get("llm", []))
        clean_regex = _mean(category_scores.get("clean", {}).get("regex", []))
        noisy_llm = _mean(
            category_scores.get("typos", {}).get("llm", [])
            + category_scores.get("voice_to_text", {}).get("llm", [])
        )
        noisy_regex = _mean(
            category_scores.get("typos", {}).get("regex", [])
            + category_scores.get("voice_to_text", {}).get("regex", [])
        )

        category_f1_pairs = {
            category: (_mean(scores["llm"]), _mean(scores["regex"]))
            for category, scores in category_scores.items()
        }

        statistics: Dict[str, Any] = {}
        if llm_correct:
            statistics["mcnemar"] = mcnemar_test(llm_correct, regex_correct)
        statistics["wilcoxon_by_category"] = wilcoxon_category_test(category_f1_pairs)
        statistics["category_mean_f1"] = category_f1_pairs

        return EvaluationSummary(
            accuracy={
                "llm_mean_f1": _mean(llm_f1_values),
                "llm_std_f1": _std(llm_f1_values),
                "regex_mean_f1": _mean(regex_f1_values),
                "regex_std_f1": _std(regex_f1_values),
            },
            robustness={
                "llm_drop": robustness_drop(clean_llm, noisy_llm),
                "regex_drop": robustness_drop(clean_regex, noisy_regex),
            },
            consistency={
                "llm_pairwise_agreement_mean": _mean(consistency_values),
                "llm_pairwise_agreement_std": _std(consistency_values),
            },
            hallucination={
                "llm_rate_mean": _mean(hallucination_llm),
                "llm_rate_std": _std(hallucination_llm),
                "regex_rate_mean": _mean(hallucination_regex),
                "regex_rate_std": _std(hallucination_regex),
            },
            statistics=statistics,
        )

    def _summary_to_dict(self, summary: EvaluationSummary) -> Dict[str, Any]:
        return {
            "accuracy": summary.accuracy,
            "robustness": summary.robustness,
            "consistency": summary.consistency,
            "hallucination": summary.hallucination,
            "statistics": summary.statistics,
        }


def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return variance ** 0.5


def load_results_summary(path: str | Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
