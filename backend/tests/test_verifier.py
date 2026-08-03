"""Unit tests for the source-grounding verifier.

These tests define the grounding rules precisely and were written and passed
BEFORE the verifier was scored against the benchmark artefacts, mirroring the
freeze-before-measurement discipline used for ground-truth labelling.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.evaluation.verifier import (
    ABSTAINED,
    GROUNDED,
    UNGROUNDED,
    ground_end_time,
    ground_location,
    ground_recurrence,
    ground_start_time,
    ground_title,
    verify_event,
)


class TestTimeGrounding:
    def test_fabricated_time_is_flagged(self):
        # The canonical fabrication case: weekday present, no clock time.
        source = "Meeting with John next Tuesday"
        assert ground_start_time("2026-08-04T09:00:00+10:00", source) is True  # date grounds start
        assert ground_end_time("2026-08-04T10:00:00+10:00", source) is False  # nothing grounds end

    def test_legitimate_time_is_not_flagged(self):
        source = "Team meeting next Tuesday at 3pm"
        assert ground_start_time("2026-08-04T15:00:00+10:00", source) is True

    def test_single_time_does_not_ground_end_time(self):
        # Default one hour end time fabrication.
        source = "Team meeting next Tuesday at 3pm"
        assert ground_end_time("2026-08-04T16:00:00+10:00", source) is False

    def test_time_range_grounds_end_time(self):
        assert ground_end_time("x", "Workshop at 1pm-5pm Friday") is True
        assert ground_end_time("x", "Work session at 9:00am - 11:30am tomorrow") is True

    def test_from_to_range_grounds_end_time(self):
        assert ground_end_time("x", "Vacation from December 20th to January 5th") is True

    def test_until_grounds_end_time(self):
        assert ground_end_time("x", "Focus block until 4pm") is True

    def test_hyphenated_words_do_not_ground_end_time(self):
        assert ground_end_time("x", "Parent-teacher meeting next Thursday") is False

    def test_spelled_out_voice_time_grounds_start(self):
        source = "call mom Sunday eight thirty aye em"
        assert ground_start_time("2026-08-09T08:30:00+10:00", source) is True

    def test_vague_ish_time_does_not_ground_clock_time(self):
        # "7ish" is vague; labelling rules set ground truth null, and the
        # verifier deliberately does not treat it as an explicit time signal.
        source = "Dinner with Sarah around 7ish"
        assert ground_end_time("x", source) is False

    def test_no_date_or_time_flags_start(self):
        source = "Lunch with the team sometime"
        assert ground_start_time("2026-08-04T12:00:00+10:00", source) is False


class TestTitleGrounding:
    def test_title_present_in_source(self):
        assert ground_title("team meeting", "Team meeting next Tuesday at 3pm") is True

    def test_title_with_typos_still_grounds(self):
        assert ground_title("team standup", "Teem standup tomorow at 9am") is True

    def test_fabricated_title_is_flagged(self):
        assert ground_title("quarterly budget review", "Coffee at 10am") is False


class TestLocationGrounding:
    def test_location_fuzzy_match(self):
        assert ground_location("bondi gym", "Yoga class Saturday 8am at Bondi Gym") is True

    def test_fabricated_location_is_flagged(self):
        assert ground_location("cbd office", "Meeting with John next Tuesday") is False


class TestRecurrenceGrounding:
    def test_none_recurrence_is_always_grounded(self):
        assert ground_recurrence("none", "Coffee at 10am") is True
        assert ground_recurrence(None, "Coffee at 10am") is True

    def test_recurrence_keyword_grounds(self):
        assert ground_recurrence("weekly", "Every Monday team meeting at 10am") is True

    def test_fabricated_recurrence_is_flagged(self):
        assert ground_recurrence("weekly", "Team meeting next Tuesday at 3pm") is False


class TestVerifyEvent:
    def test_abstained_fields_are_never_flagged(self):
        event = {
            "title": "meeting with john",
            "start_time": "2026-08-04T09:00:00+10:00",
            "end_time": None,
            "location": None,
            "notes": None,
            "recurrence_type": "none",
        }
        result = verify_event(event, "Meeting with John next Tuesday")
        assert result["end_time"] == ABSTAINED
        assert result["location"] == ABSTAINED
        assert result["notes"] == ABSTAINED
        assert result["recurrence_type"] == ABSTAINED

    def test_fabricated_fields_are_flagged(self):
        event = {
            "title": "meeting with john",
            "start_time": "2026-08-04T09:00:00+10:00",
            "end_time": "2026-08-04T10:00:00+10:00",
            "location": "office",
            "notes": None,
            "recurrence_type": "none",
        }
        result = verify_event(event, "Meeting with John next Tuesday")
        assert result["title"] == GROUNDED
        assert result["start_time"] == GROUNDED
        assert result["end_time"] == UNGROUNDED
        assert result["location"] == UNGROUNDED

    def test_fully_grounded_event(self):
        event = {
            "title": "yoga class",
            "start_time": "2026-08-08T08:00:00+10:00",
            "end_time": None,
            "location": "bondi gym",
            "notes": None,
            "recurrence_type": "none",
        }
        result = verify_event(event, "Yoga class Saturday 8am at Bondi Gym")
        assert result["title"] == GROUNDED
        assert result["start_time"] == GROUNDED
        assert result["location"] == GROUNDED
