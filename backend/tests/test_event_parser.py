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


class StubLLMParser:
    """Stands in for the live LLM so multi-event post-processing runs offline."""

    def __init__(self, *events):
        self.events = events

    async def parse(self, text, tz_name):
        return [event.model_copy() for event in self.events]


def test_multiple_events_keeps_recurring_series_as_one_event(event_parser):
    from backend.models.event_models import ParsedEvent

    text = "Create 3 standup meetings every day this week at 10am"
    event_parser.intelligent_parser = StubLLMParser(
        ParsedEvent(
            title="Standup",
            start_time="tomorrow at 10am",
            recurrence_type="daily",
            recurrence_count=3,
        )
    )
    events = asyncio.run(event_parser.parse_multiple_events(text, tz_name="Australia/Sydney"))

    # A finite series stays one RRULE event rather than 3 one-off events.
    assert len(events) == 1
    assert events[0].recurrence_type == "daily"
    assert events[0].recurrence_count == 3
    assert datetime.fromisoformat(events[0].start_time).hour == 10
    assert events[0].end_time_assumed is True
    assert events[0].original_text == text


def test_multiple_events_without_recurrence_words_are_one_offs(event_parser):
    from backend.models.event_models import ParsedEvent

    event_parser.intelligent_parser = StubLLMParser(
        ParsedEvent(title="Lunch", start_time="tomorrow at 1pm", recurrence_type="weekly"),
        ParsedEvent(title="Dinner", start_time="tomorrow at 7pm", recurrence_type="weekly"),
    )
    events = asyncio.run(
        event_parser.parse_multiple_events(
            "Lunch at 1pm and dinner at 7pm tomorrow", tz_name="Australia/Sydney"
        )
    )

    assert [event.title for event in events] == ["Lunch", "Dinner"]
    assert all(event.recurrence_type == "none" for event in events)


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
