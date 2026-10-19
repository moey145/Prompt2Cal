"""The model's dates, checked against the user's own words."""

from datetime import datetime

import pytest
import pytz

from backend.models.event_models import ParsedEvent, RecurrenceType
from backend.services.date_checks import check_event_dates, has_recurrence_evidence

SYDNEY = pytz.timezone("Australia/Sydney")
# Monday 19 October 2026, 8:53pm.
MONDAY_EVENING = SYDNEY.localize(datetime(2026, 10, 19, 20, 53))


def at(day, hour, minute=0):
    return SYDNEY.localize(datetime(2026, 10, day, hour, minute)).isoformat()


def checked(source, start, end=None, recurrence="none", **fields):
    event = ParsedEvent(
        title="Event", start_time=start, end_time=end, recurrence_type=recurrence, **fields
    )
    check_event_dates(event, source, MONDAY_EVENING)
    return event


class TestUnaskedRepeats:
    def test_a_repeat_the_text_never_asked_for_is_dropped(self):
        event = checked("Gym Monday 6am", at(26, 6), recurrence="weekly", recurrence_count=4)
        assert event.recurrence_type == RecurrenceType.NONE
        assert event.recurrence_count is None

    @pytest.mark.parametrize(
        "source",
        [
            "Gym every Monday at 6am",
            "Tennis Tuesdays at 7pm",
            "Standup weekly on Monday",
            "Mentoring fortnightly on Tuesday",
            "Class Monday for the next 6 weeks",
            "Team sync on weekdays at 9am",
        ],
    )
    def test_asked_for_repeats_are_kept(self, source):
        assert has_recurrence_evidence(source)


class TestPassedStarts:
    def test_a_named_weekday_already_gone_moves_to_next_week(self):
        event = checked("Gym Monday 6am", at(19, 6), at(19, 7))
        assert event.start_time.startswith("2026-10-26T06:00")
        assert event.end_time.startswith("2026-10-26T07:00")

    def test_a_time_with_no_date_already_gone_moves_to_tomorrow(self):
        event = checked("Meeting at 3pm at 3 Smith St", at(19, 15))
        assert event.start_time.startswith("2026-10-20T15:00")

    @pytest.mark.parametrize(
        "source", ["Dentist today at 3pm", "Call this morning at 9", "Meeting 19 October at 3pm"]
    )
    def test_today_or_an_explicit_date_is_left_alone(self, source):
        assert checked(source, at(19, 15)).start_time.startswith("2026-10-19T15:00")

    def test_future_starts_are_left_alone(self):
        assert checked("Gym Wednesday 6am", at(21, 6)).start_time.startswith("2026-10-21T06:00")


class TestSeriesStart:
    def test_until_date_is_not_taken_as_the_start(self):
        event = checked(
            "Mentoring every other Tuesday at 5pm until December",
            SYDNEY.localize(datetime(2026, 12, 1, 17)).isoformat(),
            recurrence="weekly",
            recurrence_interval=2,
            end_date="2026-12-31",
        )
        assert event.start_time.startswith("2026-10-20T17:00")
        assert event.recurrence_interval == 2
        assert event.end_date == "2026-12-31"

    @pytest.mark.parametrize(
        "source",
        [
            "Mentoring every Tuesday at 5pm starting in November",
            "Mentoring every Tuesday in November at 5pm",
            "Mentoring every Tuesday from 3 November at 5pm",
        ],
    )
    def test_a_stated_start_is_kept(self, source):
        start = SYDNEY.localize(datetime(2026, 11, 3, 17)).isoformat()
        assert checked(source, start, recurrence="weekly").start_time == start
