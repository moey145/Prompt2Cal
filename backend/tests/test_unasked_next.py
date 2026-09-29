"""The model's "next Monday" for a plain "every Monday" starts a series a week late."""

from datetime import datetime, timedelta

import pytest
import pytz

from backend.models.event_models import ParsedEvent
from backend.services.event_parser import EventParser, drop_unasked_next

TZ = pytz.timezone("Europe/London")


@pytest.mark.parametrize(
    "start_time, source, expected",
    [
        ("next Monday at 9am", "standup every Monday at 9am", "Monday at 9am"),
        ("next Tuesday at 6pm", "yoga every Tuesday at 6pm for 4 weeks", "Tuesday at 6pm"),
        # The user said "next", so it stands.
        ("next Tuesday at 1pm", "lunch next Tuesday at 1pm", "next Tuesday at 1pm"),
        # "next week" is the user's word too; leave the phrase alone.
        ("next Monday at 9am", "kickoff next week", "next Monday at 9am"),
        # Nothing to change.
        ("Monday at 9am", "standup every Monday", "Monday at 9am"),
        ("tomorrow at 3pm", "coffee tomorrow at 3pm", "tomorrow at 3pm"),
        ("", "every Monday", ""),
    ],
)
def test_drop_unasked_next(start_time, source, expected):
    assert drop_unasked_next(start_time, source) == expected


@pytest.fixture
def parser():
    return EventParser()


def test_a_weekly_series_starts_at_the_soonest_weekday(parser):
    event = ParsedEvent(
        title="Team standup",
        start_time="next Monday at 9am",
        recurrence_type="weekly",
        recurrence_count=3,
        original_text="team standup every Monday at 9am for 3 weeks",
    )
    parser._resolve_event_datetimes(
        event, TZ, source_text="team standup every Monday at 9am for 3 weeks"
    )

    start = datetime.fromisoformat(event.start_time)
    now = datetime.now(TZ)
    assert start.strftime("%A") == "Monday"
    assert start > now
    # The soonest Monday is at most a week away; a week-late start is not.
    assert start - now <= timedelta(days=7)


def test_an_explicit_next_still_means_next_week(parser):
    source = "lunch with Sarah next Tuesday at 1pm"
    event = ParsedEvent(title="Lunch", start_time="next Tuesday at 1pm", original_text=source)
    parser._resolve_event_datetimes(event, TZ, source_text=source)

    start = datetime.fromisoformat(event.start_time)
    assert start.strftime("%A") == "Tuesday"
    assert start > datetime.now(TZ)
