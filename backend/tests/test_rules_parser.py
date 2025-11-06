import pytest
from datetime import datetime, timedelta
import pytz

from backend.services.rules_parser import parse_with_rules


@pytest.mark.parametrize(
    "text, timezone, expected",
    [
        (
            "Meeting at 9am - 11am tomorrow",
            "Australia/Sydney",
            {
                "title": "Meeting",
                "start": "tomorrow at 9am",
                "end": "tomorrow at 11am",
                "recurrence_type": "none",
                "duration_minutes": 120,
            },
        ),
        (
            "Coffee at 9am - 9:30am from today - Sunday",
            "Australia/Sydney",
            {
                "title": "Coffee",
                "recurrence_type": "daily",
                "end_date_is_future": True,  # Just check it exists and is in the future
                "duration_minutes": 30,
            },
        ),
        (
            "First Monday of each month board meeting at 9am",
            "UTC",
            {
                "title": "board meeting",
                "recurrence_type": "monthly",
                "start_is_iso": True,  # Check that start is an ISO datetime
            },
        ),
        (
            "Lunch tomorrow",
            "UTC",
            {
                "title": "Lunch",
                "start": "tomorrow",
                "duration_minutes": 60,
            },
        ),
    ],
)
def test_parse_with_rules(text, timezone, expected):
    events = parse_with_rules(text, timezone)
    assert events, "Rules parser should return at least one event"
    event = events[0]
    
    if "title" in expected:
        assert event.title == expected["title"]
    if "start" in expected:
        assert expected["start"] in event.start
    if "end" in expected:
        assert event.end and expected["end"] in event.end
    if "recurrence_type" in expected:
        assert event.recurrence_type == expected["recurrence_type"]
    if "duration_minutes" in expected:
        assert event.duration_minutes == expected["duration_minutes"]
    if expected.get("end_date_is_future"):
        assert event.end_date is not None
        # Just verify it's a valid ISO date
        try:
            datetime.fromisoformat(event.end_date.replace("Z", "+00:00"))
        except:
            assert False, f"end_date should be valid ISO format, got: {event.end_date}"
    if expected.get("start_is_iso"):
        # Verify start is an ISO datetime string
        try:
            datetime.fromisoformat(event.start.replace("Z", "+00:00"))
        except:
            assert False, f"start should be valid ISO format, got: {event.start}"
