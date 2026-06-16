from __future__ import annotations

from typing import List, Tuple

from rapidfuzz import fuzz

from .models import EvalEvent

SIMILARITY_THRESHOLD = 0.7


def _title_similarity(left: EvalEvent, right: EvalEvent) -> float:
    left_title = (left.title or "").strip().lower()
    right_title = (right.title or "").strip().lower()
    if not left_title and not right_title:
        return 1.0
    if not left_title or not right_title:
        return 0.0
    return fuzz.ratio(left_title, right_title) / 100.0


def align_events(
    predicted: List[EvalEvent],
    ground_truth: List[EvalEvent],
    threshold: float = SIMILARITY_THRESHOLD,
) -> Tuple[List[Tuple[EvalEvent, EvalEvent]], List[EvalEvent], List[EvalEvent]]:
    """Greedy one-to-one assignment on normalised title similarity."""
    remaining_predictions = list(predicted)
    remaining_truth = list(ground_truth)
    pairs: List[Tuple[EvalEvent, EvalEvent]] = []

    while remaining_predictions and remaining_truth:
        best_score = -1.0
        best_pair = None

        for pred_index, pred_event in enumerate(remaining_predictions):
            for truth_index, truth_event in enumerate(remaining_truth):
                score = _title_similarity(pred_event, truth_event)
                if score > best_score:
                    best_score = score
                    best_pair = (pred_index, truth_index)

        if best_pair is None or best_score < threshold:
            break

        pred_index, truth_index = best_pair
        pairs.append((remaining_predictions.pop(pred_index), remaining_truth.pop(truth_index)))

    false_positives = remaining_predictions
    false_negatives = remaining_truth
    return pairs, false_positives, false_negatives
