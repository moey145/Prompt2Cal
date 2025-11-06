import pytest
import asyncio
from datetime import datetime, timedelta
import pytz

from backend.services.event_parser import EventParser


@pytest.fixture
def event_parser():
    return EventParser()


@pytest.mark.parametrize(
    "text, validator",
    [
        (
            "Meeting at 9am - 11am tomorrow",
            lambda event: (
                event.duration_minutes == 120 and
                datetime.fromisoformat(event.end_time.replace("Z", "+00:00")) >
                datetime.fromisoformat(event.start_time.replace("Z", "+00:00"))
            ),
        ),
        (
            "Coffee at 9am - 9:30am from today - Sunday",
            lambda event: (
                event.recurrence_type == "daily" and
                event.end_date is not None
            ),
        ),
        (
            "First Monday of each month board meeting at 9am",
            lambda event: event.recurrence_type == "monthly",
        ),
        (
            "Doctors appointment",
            lambda event: event.duration_minutes == 60,
        ),
    ],
)
def test_event_parser_rules_first(event_parser, text, validator):
    event = asyncio.run(event_parser.parse_event_text(text))
    assert validator(event), f"Validation failed for: {text}\nGot event: {event}"


@pytest.mark.parametrize(
    "text, expected_count",
    [
        (
            "Create 3 standup meetings every day this week at 10am",
            3,
        ),
    ],
)
def test_event_parser_bulk(event_parser, text, expected_count):
    events = asyncio.run(event_parser.parse_bulk_events(text))
    assert len(events) == expected_count, f"Expected {expected_count} events, got {len(events)}"
