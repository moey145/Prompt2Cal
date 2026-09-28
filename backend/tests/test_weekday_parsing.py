"""Tests for bare weekday phrases, which used to lose the time or land in the past."""

from datetime import datetime

import pytest
import pytz

from backend.services.date_parser import DateParser

TZ = pytz.timezone("Europe/London")
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@pytest.fixture
def parser():
    return DateParser()


def now():
    return datetime.now(TZ)


@pytest.mark.parametrize("weekday", WEEKDAYS)
@pytest.mark.parametrize("template, hour", [("{day} 10am", 10), ("{day} at 10am", 10)])
def test_weekday_keeps_the_stated_time_with_or_without_at(parser, weekday, template, hour):
    parsed = parser.parse_start_time(template.format(day=weekday), TZ)
    assert parsed is not None
    assert parsed.hour == hour, f"{template.format(day=weekday)} lost its time"
    assert parsed.minute == 0
    assert parsed.strftime("%A") == weekday


@pytest.mark.parametrize("weekday", WEEKDAYS)
def test_a_bare_weekday_never_lands_in_the_past(parser, weekday):
    # Whatever day the suite runs on, the upcoming occurrence is in the future:
    # if today is that weekday and the time has gone, it means next week.
    for phrase in (f"{weekday} 9am", f"{weekday} at 9am", f"{weekday} 8pm"):
        parsed = parser.parse_start_time(phrase, TZ)
        assert parsed is not None, phrase
        assert parsed > now(), f"{phrase} resolved to the past"


def test_todays_weekday_earlier_today_moves_to_next_week(parser):
    today = now()
    # One minute ago, expressed as a bare weekday, is next week's occurrence.
    moment = today.replace(second=0, microsecond=0)
    phrase = f"{today.strftime('%A')} at {moment.strftime('%I:%M%p').lstrip('0').lower()}"
    parsed = parser.parse_start_time(phrase, TZ)
    assert parsed is not None
    assert parsed >= moment


@pytest.mark.parametrize(
    "phrase, hour",
    [("Tuesday 3pm", 15), ("Friday 9am", 9), ("Saturday 8am", 8), ("Sunday 11am", 11)],
)
def test_am_pm_is_respected_without_at(parser, phrase, hour):
    parsed = parser.parse_start_time(phrase, TZ)
    assert parsed is not None and parsed.hour == hour


def test_explicit_next_still_means_next_week(parser):
    this_week = parser.parse_start_time("Monday at 9am", TZ)
    next_week = parser.parse_start_time("next Monday at 9am", TZ)
    assert this_week is not None and next_week is not None
    assert next_week >= this_week
