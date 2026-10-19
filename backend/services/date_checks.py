"""Checks on the model's dates against what the user actually wrote.

The model's start is a phrase like "this Monday at 6am", which on a Monday
evening resolves to a time already gone; it sometimes adds a weekly repeat
nobody asked for; and in "every other Tuesday until December" it can take
December as the start. Each check here only acts when the text backs it up.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from ..models.event_models import RecurrenceType
from .weekday_split import next_on_weekday, says_recurring

_FULL_DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_WEEKDAY = re.compile(rf"\b({'|'.join(_FULL_DAYS)})s?\b", re.IGNORECASE)
_RECURRENCE_WORDS = re.compile(
    r"\b(?:every|each|daily|weekly|fortnightly|biweekly|monthly|yearly|annually"
    r"|recurring|weekdays|weekends)\b"
    r"|\b(?:for\s+(?:the\s+)?)?next\s+(?:\d+|two|three|four|five|six|seven|eight|nine|ten)"
    r"\s+(?:weeks?|months?)\b",
    re.IGNORECASE,
)
# Words that pin the day to today, so a passed time stays where it is.
_TODAY = re.compile(r"\b(?:today|tonight|now|this\s+(?:morning|afternoon|evening))\b", re.IGNORECASE)
# Anything naming a date, not only a time: a weekday, month, relative day or
# numeric date.
_DATE = re.compile(
    rf"\b(?:{'|'.join(_FULL_DAYS)}|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)s?\b"
    r"|\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
    r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b"
    r"|\b(?:today|tonight|tomorrow|tmrw|weekend|week|month|year|fortnight)\b"
    r"|\b\d{1,2}(?:st|nd|rd|th)\b|\b\d{1,2}/\d{1,2}\b|\bin\s+\d+\s+\w+",
    re.IGNORECASE,
)
# Words that say when a series begins; without them it begins next time round.
_STATED_START = re.compile(r"\b(?:start(?:s|ing)?|from|beginning|commencing|next|after)\b", re.IGNORECASE)
_UNTIL_CLAUSE = re.compile(r"\b(?:until|till|through|ending|ends?)\b.*$", re.IGNORECASE)


def has_recurrence_evidence(source: str) -> bool:
    """True when the text asks for a repeat, so a series isn't the model's guess."""
    return bool(source and (says_recurring(source) or _RECURRENCE_WORDS.search(source)))


def _named_weekdays(text: str) -> set:
    return {_FULL_DAYS.index(m.group(1).lower()) for m in _WEEKDAY.finditer(text)}


def series_start(start: datetime, source: str, now: datetime) -> Optional[datetime]:
    """The next occurrence for "every Tuesday until December", if the model moved it.

    Only for a series on one named weekday whose text says nothing about when
    it begins: no start word, and no date outside the "until ..." part.
    """
    before_until = _UNTIL_CLAUSE.sub("", source)
    days = _named_weekdays(before_until)
    if len(days) != 1 or _STATED_START.search(before_until):
        return None
    if _DATE.search(_WEEKDAY.sub("", before_until)):
        return None
    expected = next_on_weekday(days.pop(), start.hour, start.minute, now)
    return expected if expected != start else None


def move_past_start(start: datetime, source: str, now: datetime) -> Optional[timedelta]:
    """How far to move a start that has already passed, or None to leave it.

    A weekday the user named moves on a week ("Gym Monday 6am" said on Monday
    evening is next Monday). A time with no date at all moves on a day
    ("Meeting at 3pm" said at 9pm is tomorrow). Anything else, including
    "today", an explicit date, or a start more than a day gone, is left alone.
    """
    if start >= now or now - start > timedelta(days=1) or _TODAY.search(source):
        return None
    if start.weekday() in _named_weekdays(source):
        return timedelta(days=7)
    if not _DATE.search(source):
        return timedelta(days=1)
    return None


def check_event_dates(event, source: str, now: datetime) -> None:
    """Apply the checks above to a resolved event, in place."""
    recurrence = str(getattr(event.recurrence_type, "value", event.recurrence_type) or "none").lower()
    if recurrence != "none" and not has_recurrence_evidence(source):
        event.recurrence_type = RecurrenceType.NONE
        event.recurrence_count = None
        event.recurrence_interval = 1
        event.end_date = None
        recurrence = "none"

    start, end = _parse(event.start_time), _parse(event.end_time)
    if not start:
        return
    shift = None
    if recurrence == "weekly":
        anchored = series_start(start, source, now)
        if anchored:
            shift = anchored - start
    if shift is None:
        shift = move_past_start(start, source, now)
    if shift:
        event.start_time = (start + shift).isoformat()
        if end:
            event.end_time = (end + shift).isoformat()


def _parse(value) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(value)) if value else None
    except ValueError:
        return None
