import pytest

from backend.evaluation.alignment import align_events
from backend.evaluation.metrics import (
    f1_for_input,
    hallucination_rate,
    input_is_fully_correct,
    pairwise_consistency,
    robustness_drop,
)
from backend.evaluation.models import EvalEvent


def _event(**kwargs) -> EvalEvent:
    return EvalEvent(**kwargs)


def test_align_events_matches_similar_titles():
    predicted = [_event(title="Team meeting", start_time="2026-05-20T15:00:00+10:00")]
    ground_truth = [_event(title="team meeting", start_time="2026-05-20T15:00:00+10:00")]
    pairs, false_positives, false_negatives = align_events(predicted, ground_truth)
    assert len(pairs) == 1
    assert not false_positives
    assert not false_negatives


def test_f1_perfect_match():
    event = _event(
        title="lunch",
        start_time="2026-05-20T13:00:00+10:00",
        end_time=None,
        location=None,
        notes=None,
        recurrence_type="none",
    )
    score = f1_for_input([event], [event])
    assert score == 1.0


def test_hallucination_counts_fabricated_null_fields():
    predicted = [_event(title="meeting", start_time="2026-05-20T09:00:00+10:00")]
    ground_truth = [_event(title="meeting", start_time=None)]
    rate = hallucination_rate(predicted, ground_truth)
    # Denominator = all GT-null fields (start/end/location/notes); only start_time was fabricated.
    assert rate == 0.25


def test_input_is_fully_correct_requires_all_fields():
    predicted = [_event(title="meeting", start_time="2026-05-20T09:00:00+10:00")]
    ground_truth = [_event(title="meeting", start_time="2026-05-20T09:00:00+10:00")]
    assert input_is_fully_correct(predicted, ground_truth) is True


def test_pairwise_consistency():
    run_a = [_event(title="coffee", start_time="2026-05-20T10:00:00+10:00")]
    run_b = [_event(title="coffee", start_time="2026-05-20T10:00:00+10:00")]
    run_c = [_event(title="coffee", start_time="2026-05-20T11:00:00+10:00")]
    # Three runs → three pairs; only (A, B) agree.
    assert pairwise_consistency([run_a, run_b, run_c]) == pytest.approx(1 / 3)


def test_robustness_drop():
    assert robustness_drop(0.8, 0.6) == pytest.approx(0.25)
