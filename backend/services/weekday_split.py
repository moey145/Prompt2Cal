"""One activity on several weekdays: "Gym Mon Wed Fri at 6am".

The model tends to return a single event for the first day named, so the
other days are dropped. These helpers find the days the user listed and give
each its own event, on the next date that day comes round.
"""

import re
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from ..models.event_models import RecurrenceType

_FULL = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_SHORT = {
    "mon": 0, "tue": 1, "tues": 1, "wed": 2, "weds": 2,
    "thu": 3, "thur": 3, "thurs": 3, "fri": 4, "sat": 5, "sun": 6,
}
_DAY_INDEX = {**{name: i for i, name in enumerate(_FULL)}, **_SHORT}

_FULL_DAY = r"(?:" + "|".join(_FULL) + r")s?"
_ANY_DAY = r"(?:" + "|".join(_FULL) + "|" + "|".join(sorted(_SHORT, key=len, reverse=True)) + r")s?"
_DAY_TOKEN = re.compile(rf"\b({_ANY_DAY})\b", re.IGNORECASE)
_FULL_DAY_TOKEN = re.compile(rf"\b({_FULL_DAY})\b", re.IGNORECASE)
# Two or more days in a row: "Mon Wed Fri", "Mon/Wed", "Tue, Thu and Sat".
_DAY_LIST = re.compile(
    rf"\b{_ANY_DAY}(?:\s*(?:,|/|&|\band\b|\s)\s*{_ANY_DAY})+\b", re.IGNORECASE
)
# "Monday to Friday" or "Mon-Fri" names a span, not a list of days.
_DAY_SPAN = re.compile(
    rf"\b{_ANY_DAY}\s*(?:-|–|\bto\b|\bthrough\b|\bthru\b|\buntil\b|\btill\b)\s*{_ANY_DAY}\b",
    re.IGNORECASE,
)
# Start times only: the end of a range ("6:30am to 8am") is not another start.
_START_TIMES = re.compile(
    r"(?<![-–]\s)(?<![-–])(?<!\bto\s)(?<!until\s)(?<!till\s)"
    r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b",
    re.IGNORECASE,
)
_PLURAL_DAY = re.compile(rf"\b(?:{'|'.join(_FULL)})s\b", re.IGNORECASE)
_RECURRING = re.compile(
    r"\b(?:every|each|weekly|daily|monthly)\b"
    r"|\bfor\s+\d+\s+(?:weeks?|months?|days?)\b"
    r"|\buntil\b",
    re.IGNORECASE,
)


def _day_index(token: str) -> int:
    token = token.lower()
    if token not in _DAY_INDEX and token.endswith("s"):
        token = token[:-1]
    return _DAY_INDEX[token]


def mentioned_weekdays(text: str) -> List[int]:
    """The distinct weekdays the text lists, in the order written (Monday = 0).

    Full names count wherever they appear. Short names ("sat", "sun", "wed")
    are ordinary words too, so they count only inside a list of days, and not
    after "the" ("in the sun Saturday").
    """
    if not text or _DAY_SPAN.search(text):
        return []
    found = []
    for match in _FULL_DAY_TOKEN.finditer(text):
        found.append((match.start(), _day_index(match.group(1))))
    for run in _DAY_LIST.finditer(text):
        if re.search(r"\bthe\s+$", text[: run.start()], re.IGNORECASE):
            continue
        for match in _DAY_TOKEN.finditer(run.group(0)):
            found.append((run.start() + match.start(), _day_index(match.group(1))))
    days = []
    for _, day in sorted(found):
        if day not in days:
            days.append(day)
    return days


def says_recurring(text: str) -> bool:
    """True when the text asks for a series: "every", "weekly", "Mondays"..."""
    return bool(text and (_RECURRING.search(text) or _PLURAL_DAY.search(text)))


def next_on_weekday(weekday: int, hour: int, minute: int, now: datetime) -> datetime:
    """The next time that weekday comes round at hour:minute, after now."""
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    candidate += timedelta(days=(weekday - now.weekday()) % 7)
    if candidate <= now:
        candidate += timedelta(days=7)
    return candidate


def _read_start(event, local_tz, parse_phrase) -> Optional[datetime]:
    try:
        start = datetime.fromisoformat(str(event.start_time))
    except ValueError:
        start = parse_phrase(str(event.start_time or ""))
    if not start:
        return None
    return start.astimezone(local_tz) if start.tzinfo else local_tz.localize(start)


def _repeat_fields(recurring: bool) -> dict:
    if recurring:
        return {"recurrence_type": RecurrenceType.WEEKLY}
    return {
        "recurrence_type": RecurrenceType.NONE,
        "recurrence_count": None,
        "recurrence_interval": 1,
        "end_date": None,
    }


def _one_shared_time(events: list, text: str, starts: list) -> bool:
    """True when every listed day shares one start time.

    "Monday at 9am, and Wednesday at 5pm" has a time per day, and one time
    can't stand in for both, whether the model gave one event or two.
    """
    if None in starts or len({(s.hour, s.minute) for s in starts}) != 1:
        return False
    return len(events) > 1 or len(_START_TIMES.findall(text)) <= 1


def split_by_weekday(
    events: list,
    text: str,
    local_tz,
    parse_phrase: Callable[[str], Optional[datetime]],
    now: Optional[datetime] = None,
) -> list:
    """One event per listed weekday, when the events are one activity.

    Returns the events unchanged when fewer than two days are listed, when the
    model already gave different activities ("Yoga Mon, swim Wed") or times,
    or when the start time can't be read. A series ("every", "Mondays")
    becomes a weekly series per day; otherwise each day is a one-off.
    """
    days = mentioned_weekdays(text)
    if len(days) < 2 or not events or len(events) > len(days):
        return events
    if len({(event.title or "").strip().lower() for event in events}) != 1:
        return events
    starts = [_read_start(event, local_tz, parse_phrase) for event in events]
    if not _one_shared_time(events, text, starts):
        return events

    start = starts[0]
    now = now or datetime.now(local_tz)
    use_next = bool(re.search(rf"\bnext\s+{_ANY_DAY}\b", text, re.IGNORECASE))
    time_phrase = start.strftime("%I:%M%p").lstrip("0").lower()

    day_starts = []
    for day in days:
        if use_next:
            # "next Mon and Wed" keeps the meaning the rest of the parser gives "next".
            day_start = parse_phrase(f"next {_FULL[day]} at {time_phrase}")
        else:
            day_start = next_on_weekday(day, start.hour, start.minute, now)
        if not day_start:
            return events
        day_starts.append(day_start)

    repeat = _repeat_fields(says_recurring(text))
    return [
        events[0].model_copy(
            update={"start_time": day_start.isoformat(), "end_time": None, **repeat}
        )
        for day_start in sorted(day_starts)
    ]
