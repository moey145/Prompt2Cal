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


def test_resolve_event_datetimes_preserves_multi_day_range(event_parser):
    tz = pytz.timezone("Australia/Sydney")
    from backend.models.event_models import ParsedEvent

    event = ParsedEvent(
        title="Vacation",
        start_time="December 20th at 9am",
        end_time="January 5th at 5pm",
        duration_minutes=60,
        recurrence_type="none",
    )
    event_parser._resolve_event_datetimes(event, tz)

    start = datetime.fromisoformat(event.start_time)
    end = datetime.fromisoformat(event.end_time)
    assert end > start + timedelta(days=1)
    assert start.month == 12 and start.day == 20
    assert end.month == 1 and end.day == 5
    assert event.end_time_assumed is False


def test_stated_duration_is_not_assumed(event_parser):
    tz = pytz.timezone("Australia/Sydney")
    from backend.models.event_models import ParsedEvent

    event = ParsedEvent(
        title="Gym",
        start_time="next Monday at 6:30am",
        end_time=None,
        duration_minutes=60,
        recurrence_type="weekly",
        original_text="Gym every Monday at 6:30am for 2 hours",
    )
    event_parser._resolve_event_datetimes(
        event, tz, source_text="Gym every Monday at 6:30am for 2 hours"
    )

    start = datetime.fromisoformat(event.start_time)
    end = datetime.fromisoformat(event.end_time)
    assert event.duration_minutes == 120
    assert end - start == timedelta(hours=2)
    assert event.end_time_assumed is False


def test_default_hour_is_assumed_without_end(event_parser):
    tz = pytz.timezone("Australia/Sydney")
    from backend.models.event_models import ParsedEvent

    event = ParsedEvent(
        title="Meeting with Sarah",
        start_time="tomorrow at 3pm",
        end_time=None,
        duration_minutes=60,
        recurrence_type="none",
        original_text="Meeting with Sarah tomorrow at 3pm in the office",
    )
    event_parser._resolve_event_datetimes(
        event, tz, source_text="Meeting with Sarah tomorrow at 3pm in the office"
    )

    assert event.end_time_assumed is True


def test_explicit_end_range_is_not_assumed(event_parser):
    tz = pytz.timezone("Australia/Sydney")
    from backend.models.event_models import ParsedEvent

    event = ParsedEvent(
        title="Gym",
        start_time="next Monday at 6:30am",
        end_time="next Monday at 8:00am",
        duration_minutes=90,
        recurrence_type="weekly",
        original_text="Gym every Monday at 6:30am to 8am",
    )
    event_parser._resolve_event_datetimes(
        event, tz, source_text="Gym every Monday at 6:30am to 8am"
    )

    assert event.end_time_assumed is False
    start = datetime.fromisoformat(event.start_time)
    end = datetime.fromisoformat(event.end_time)
    assert end.hour == 8
    assert start.hour == 6
