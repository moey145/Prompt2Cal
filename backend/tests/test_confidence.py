"""Unit tests for the production per-field confidence layer."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.confidence import CORROBORATED, attach_confidence


def make_event(**overrides):
    event = {
        "title": "Team meeting",
        "start_time": "2026-08-04T15:00:00+10:00",
        "end_time": "2026-08-04T16:00:00+10:00",
        "location": None,
        "notes": None,
        "recurrence_type": "none",
    }
    event.update(overrides)
    return event


class TestVerifierIntegration:
    def test_fabricated_end_time_is_flagged(self):
        # No clock time and no range evidence in the source.
        event = make_event(title="Meeting with John")
        result = attach_confidence(event, "Meeting with John next Tuesday")
        assert result["field_confidence"]["end_time"] == "ungrounded"

    def test_fabricated_location_is_flagged(self):
        event = make_event(location="Conference Room B")
        result = attach_confidence(event, "Team meeting tomorrow at 3pm")
        assert result["field_confidence"]["location"] == "ungrounded"

    def test_null_fields_are_abstained(self):
        event = make_event()
        result = attach_confidence(event, "Team meeting tomorrow at 3pm")
        assert result["field_confidence"]["location"] == "abstained"
        assert result["field_confidence"]["notes"] == "abstained"

    def test_grounded_title(self):
        event = make_event()
        result = attach_confidence(event, "Team meeting tomorrow at 3pm")
        assert result["field_confidence"]["title"] in ("grounded", CORROBORATED)


class TestDurationRefinement:
    def test_stated_duration_grounds_end_time(self):
        # Research verifier would flag this end time (single time signal, no
        # range), but the production layer accepts a stated duration.
        event = make_event(end_time="2026-08-04T17:00:00+10:00")
        result = attach_confidence(event, "Team meeting tomorrow at 3pm for 2 hours")
        assert result["field_confidence"]["end_time"] == "grounded"

    def test_to_end_time_grounds_end_time(self):
        event = make_event(end_time="2026-08-31T08:00:00+10:00")
        result = attach_confidence(event, "Gym every Monday at 6:30am to 8am")
        assert result["field_confidence"]["end_time"] == "grounded"

    def test_weekday_next_months_grounds_weekly(self):
        event = make_event(
            title="Meeting",
            recurrence_type="weekly",
            end_time="2026-08-31T23:00:00+10:00",
        )
        result = attach_confidence(
            event,
            "Monday for the next 6 months meeting at 10pm - 11pm",
        )
        assert result["field_confidence"]["recurrence_type"] == "grounded"

    def test_no_duration_no_range_stays_ungrounded(self):
        event = make_event()
        result = attach_confidence(event, "Team meeting tomorrow at 3pm")
        assert result["field_confidence"]["end_time"] == "ungrounded"


class TestRegexCorroboration:
    def test_time_range_can_be_corroborated(self):
        # "3pm - 4pm tomorrow" is parseable by the rules parser, so when the
        # LLM extracts the same times they should be upgraded.
        event = make_event(
            title="Team meeting",
            start_time="2026-08-04T15:00:00+10:00",
            end_time="2026-08-04T16:00:00+10:00",
        )
        result = attach_confidence(
            event,
            "Team meeting tomorrow at 3pm - 4pm",
            tz_name="Australia/Sydney",
        )
        confidence = result["field_confidence"]
        # Both times are at minimum grounded (two time signals); corroborated
        # when the rules parser resolves to the same instants.
        assert confidence["start_time"] in ("grounded", CORROBORATED)
        assert confidence["end_time"] in ("grounded", CORROBORATED)

    def test_confidence_never_raises(self):
        # Robustness at the boundary: junk values must not break the layer.
        event = make_event(start_time=None, end_time=None, title="")
        result = attach_confidence(event, "")
        assert "field_confidence" in result or result is event
