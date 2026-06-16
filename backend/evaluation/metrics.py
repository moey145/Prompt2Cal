from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .alignment import align_events
from .models import EVAL_FIELDS, EvalEvent
from .normalize import events_equal, field_matches, normalize_event_list


@dataclass
class FieldScore:
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0

    @property
    def precision(self) -> float:
        if self.true_positive + self.false_positive == 0:
            return 0.0
        return self.true_positive / (self.true_positive + self.false_positive)

    @property
    def recall(self) -> float:
        if self.true_positive + self.false_negative == 0:
            return 0.0
        return self.true_positive / (self.true_positive + self.false_negative)

    @property
    def f1(self) -> float:
        precision = self.precision
        recall = self.recall
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)


def _score_field(predicted: Optional[str], expected: Optional[str], score: FieldScore) -> None:
    if field_matches(predicted, expected):
        score.true_positive += 1
        return

    if predicted is not None and expected is None:
        score.false_positive += 1
        return

    if predicted is None and expected is not None:
        score.false_negative += 1
        return

    score.false_positive += 1
    score.false_negative += 1


def score_aligned_pair(predicted: EvalEvent, expected: EvalEvent) -> FieldScore:
    score = FieldScore()
    predicted_dict = predicted.to_dict()
    expected_dict = expected.to_dict()
    for field_name in EVAL_FIELDS:
        _score_field(predicted_dict[field_name], expected_dict[field_name], score)
    return score


def merge_scores(scores: Iterable[FieldScore]) -> FieldScore:
    merged = FieldScore()
    for score in scores:
        merged.true_positive += score.true_positive
        merged.false_positive += score.false_positive
        merged.false_negative += score.false_negative
    return merged


def f1_for_input(predicted: List[EvalEvent], expected: List[EvalEvent]) -> float:
    pairs, false_positives, false_negatives = align_events(predicted, expected)
    scores = [score_aligned_pair(pred, truth) for pred, truth in pairs]

    for _ in false_positives:
        scores.append(FieldScore(false_positive=len(EVAL_FIELDS)))
    for _ in false_negatives:
        scores.append(FieldScore(false_negative=len(EVAL_FIELDS)))

    if not scores:
        return 1.0 if not predicted and not expected else 0.0

    return merge_scores(scores).f1


def input_is_fully_correct(predicted: List[EvalEvent], expected: List[EvalEvent]) -> bool:
    pairs, false_positives, false_negatives = align_events(predicted, expected)
    if false_positives or false_negatives:
        return False
    if not pairs and not predicted and not expected:
        return True
    for predicted_event, expected_event in pairs:
        predicted_dict = predicted_event.to_dict()
        expected_dict = expected_event.to_dict()
        if any(
            not field_matches(predicted_dict[field], expected_dict[field])
            for field in EVAL_FIELDS
        ):
            return False
    return bool(pairs)


def hallucination_rate(predicted: List[EvalEvent], expected: List[EvalEvent]) -> Optional[float]:
    pairs, false_positives, _ = align_events(predicted, expected)
    opportunities = 0
    fabrications = 0

    for predicted_event, expected_event in pairs:
        predicted_dict = predicted_event.to_dict()
        expected_dict = expected_event.to_dict()
        for field_name in EVAL_FIELDS:
            if expected_dict[field_name] is None:
                opportunities += 1
                if predicted_dict[field_name] is not None:
                    fabrications += 1

    for predicted_event in false_positives:
        opportunities += len(EVAL_FIELDS)
        fabrications += sum(1 for value in predicted_event.to_dict().values() if value is not None)

    if opportunities == 0:
        return None
    return fabrications / opportunities


def pairwise_consistency(runs: List[List[EvalEvent]]) -> float:
    if len(runs) < 2:
        return 1.0

    agreements = []
    for left_index in range(len(runs)):
        for right_index in range(left_index + 1, len(runs)):
            agreements.append(1.0 if events_equal(runs[left_index], runs[right_index]) else 0.0)
    return sum(agreements) / len(agreements)


def robustness_drop(clean_f1: float, noisy_f1: float) -> float:
    if clean_f1 == 0:
        return 0.0
    return (clean_f1 - noisy_f1) / clean_f1


def mcnemar_test(llm_correct: List[bool], regex_correct: List[bool]) -> Dict[str, float]:
    from statsmodels.stats.contingency_tables import mcnemar

    if len(llm_correct) != len(regex_correct):
        raise ValueError("McNemar test requires paired observations of equal length.")

    both_correct = sum(1 for llm, regex in zip(llm_correct, regex_correct) if llm and regex)
    llm_only = sum(1 for llm, regex in zip(llm_correct, regex_correct) if llm and not regex)
    regex_only = sum(1 for llm, regex in zip(llm_correct, regex_correct) if regex and not llm)
    both_wrong = sum(1 for llm, regex in zip(llm_correct, regex_correct) if not llm and not regex)

    if llm_only + regex_only == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "llm_only_correct": float(llm_only),
            "regex_only_correct": float(regex_only),
        }

    table = [[both_correct, llm_only], [regex_only, both_wrong]]
    result = mcnemar(table, exact=False, correction=True)
    return {
        "statistic": float(result.statistic),
        "p_value": float(result.pvalue),
        "llm_only_correct": float(llm_only),
        "regex_only_correct": float(regex_only),
    }


def wilcoxon_category_test(category_f1_values: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    from scipy.stats import wilcoxon

    if not category_f1_values:
        return {"statistic": 0.0, "p_value": 1.0}

    llm_values = [values[0] for values in category_f1_values.values()]
    regex_values = [values[1] for values in category_f1_values.values()]
    if len(llm_values) < 2:
        return {"statistic": 0.0, "p_value": 1.0}

    result = wilcoxon(llm_values, regex_values)
    return {"statistic": float(result.statistic), "p_value": float(result.pvalue)}
