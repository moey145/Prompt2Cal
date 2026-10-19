"""One activity on several weekdays becomes an event per day."""

from datetime import datetime

import pytest
import pytz

from backend.models.event_models import ParsedEvent, RecurrenceType
from backend.services.weekday_split import (
    mentioned_weekdays,
    next_on_weekday,
    says_recurring,
    split_by_weekday,
)

SYDNEY = pytz.timezone("Australia/Sydney")
# Monday 19 October 2026, 2pm: this morning's 6am has already gone.
MONDAY_AFTERNOON = SYDNEY.localize(datetime(2026, 10, 19, 14, 0))


def event(title, start, recurrence="none"):
    return ParsedEvent(title=title, start_time=start, recurrence_type=recurrence)


def split(events, text, now=MONDAY_AFTERNOON):
    return split_by_weekday(events, text, SYDNEY, lambda phrase: None, now=now)


@pytest.mark.parametrize(
    "text, days",
    [
        ("Gym Mon Wed Fri at 6am", [0, 2, 4]),
        ("Gym Mon/Wed/Fri 6am", [0, 2, 4]),
        ("Tennis Tue, Thu and Sat at 7pm", [1, 3, 5]),
        ("Lunch Saturday and Sunday at 1pm", [5, 6]),
        ("Tennis Tuesdays and Thursdays at 7pm", [1, 3]),
        ("Friday drinks then Monday standup", [4, 0]),
    ],
)
def test_listed_days(text, days):
    assert mentioned_weekdays(text) == days


@pytest.mark.parametrize(
    "text",
    [
        "Standup Monday to Friday at 9am",
        "Standup Mon-Fri at 9am",
        "Picnic in the sun Saturday at noon",
        "Wed the sat nav to the car",
        "Lunch on Friday at 1pm",
    ],
)
def test_spans_and_ordinary_words_are_not_a_list(text):
    assert len(mentioned_weekdays(text)) < 2


def test_plural_days_and_every_ask_for_a_series():
    assert says_recurring("Tennis Tuesdays and Thursdays at 7pm")
    assert says_recurring("Team meeting every Monday and Wednesday at 9am")
    assert not says_recurring("Gym Mon Wed Fri at 6am")
    assert not says_recurring("Everyone's lunch Friday")


def test_next_on_weekday_skips_a_time_already_gone():
    assert next_on_weekday(0, 6, 0, MONDAY_AFTERNOON).date().isoformat() == "2026-10-26"
    assert next_on_weekday(0, 18, 0, MONDAY_AFTERNOON).date().isoformat() == "2026-10-19"
    assert next_on_weekday(2, 6, 0, MONDAY_AFTERNOON).date().isoformat() == "2026-10-21"


def test_each_day_gets_its_own_upcoming_event():
    # The model returned one weekly event on this morning's Monday.
    events = [event("Gym", "2026-10-19T06:00:00+11:00", "weekly")]

    result = split(events, "Gym Mon Wed Fri at 6am")

    assert [e.start_time[:16] for e in result] == [
        "2026-10-21T06:00",
        "2026-10-23T06:00",
        "2026-10-26T06:00",
    ]
    assert all(e.title == "Gym" for e in result)
    # No "every", so these are one-offs, not a series nobody asked for.
    assert all(e.recurrence_type == RecurrenceType.NONE for e in result)
    assert all(e.end_time is None for e in result)


def test_a_series_on_several_days_is_a_weekly_series_per_day():
    events = [event("Team meeting", "2026-10-26T09:00:00+11:00", "weekly")]

    result = split(events, "Team meeting every Monday and Wednesday at 9am")

    assert [e.start_time[:16] for e in result] == ["2026-10-21T09:00", "2026-10-26T09:00"]
    assert all(e.recurrence_type == RecurrenceType.WEEKLY for e in result)


def test_different_times_per_day_are_left_alone():
    one = [event("Standup", "2026-10-26T09:00:00+11:00", "weekly")]
    two = one + [event("Standup", "2026-10-21T17:00:00+11:00", "weekly")]
    text = "Standup every Monday at 9am, and Wednesday at 5pm"

    assert split(one, text) == one
    assert split(two, text) == two


def test_different_activities_are_left_alone():
    events = [
        event("Yoga", "2026-10-26T07:00:00+11:00"),
        event("Swim", "2026-10-21T07:00:00+11:00"),
    ]
    assert split(events, "Yoga Mon, swim Wed at 7am") == events


def test_a_time_range_counts_as_one_start():
    events = [event("Gym", "2026-10-19T06:00:00+11:00")]
    result = split(events, "Gym Mon Wed 6am - 7am")
    assert len(result) == 2
