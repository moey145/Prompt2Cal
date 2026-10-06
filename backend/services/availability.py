"""Free/busy arithmetic shared by both calendar providers.

The Google service grew its own slot finding inside find_alternative_times;
Outlook had none. These functions work on plain (start, end) pairs so either
provider can feed them whatever its API returns.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Sequence, Tuple

Block = Tuple[datetime, datetime]

DEFAULT_STEP_MINUTES = 15


def merge_busy(blocks: Iterable[Block]) -> List[Block]:
    """Sort busy periods and join the ones that touch or overlap."""
    ordered = sorted((b for b in blocks if b[0] < b[1]), key=lambda b: b[0])
    merged: List[Block] = []
    for start, end in ordered:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def is_free(busy: Sequence[Block], start: datetime, end: datetime) -> bool:
    return all(end <= b_start or start >= b_end for b_start, b_end in busy)


def free_slots(
    busy: Iterable[Block],
    window_start: datetime,
    window_end: datetime,
    duration_minutes: int,
    working_hours: Optional[Tuple[int, int]] = None,
    buffer_minutes: int = 0,
    step_minutes: int = DEFAULT_STEP_MINUTES,
    limit: int = 20,
    weekdays_only: bool = False,
) -> List[Block]:
    """Every slot of the given length that fits in the window without clashing.

    Times are judged in the window's own timezone, so working hours mean the
    user's working hours only when the window carries the user's zone.
    """
    if duration_minutes <= 0 or window_end <= window_start:
        return []

    padded = [
        (start - timedelta(minutes=buffer_minutes), end + timedelta(minutes=buffer_minutes))
        for start, end in busy
    ]
    merged = merge_busy(padded)
    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)

    slots: List[Block] = []
    cursor = _round_up(window_start, step_minutes)
    while cursor + duration <= window_end and len(slots) < limit:
        slot_end = cursor + duration
        if (
            not (weekdays_only and cursor.weekday() >= 5)
            and _within_working_hours(cursor, slot_end, working_hours)
            and is_free(merged, cursor, slot_end)
        ):
            slots.append((cursor, slot_end))
            cursor = slot_end
        else:
            cursor += step
    return slots


def spread_by_day(slots: Sequence[Block], per_day: int) -> List[Block]:
    """At most per_day slots for each day, spaced across the day.

    Without this, a search over several days fills its limit with one
    morning's back-to-back slots and never reaches the later days.
    """
    if per_day <= 0:
        return []
    by_day: dict = {}
    for slot in slots:
        by_day.setdefault(slot[0].date(), []).append(slot)
    spread: List[Block] = []
    for day_slots in by_day.values():
        count = len(day_slots)
        if count <= per_day:
            spread.extend(day_slots)
        elif per_day == 1:
            spread.append(day_slots[0])
        else:
            picks = sorted({round(i * (count - 1) / (per_day - 1)) for i in range(per_day)})
            spread.extend(day_slots[i] for i in picks)
    return spread


def nearest_alternatives(
    busy: Iterable[Block],
    proposed_start: datetime,
    duration_minutes: int,
    search_hours: int = 3,
    buffer_minutes: int = 0,
    step_minutes: int = DEFAULT_STEP_MINUTES,
) -> List[Block]:
    """The closest free slot before the clash and the closest after it."""
    if duration_minutes <= 0:
        return []

    merged = merge_busy(
        (start - timedelta(minutes=buffer_minutes), end + timedelta(minutes=buffer_minutes))
        for start, end in busy
    )
    duration = timedelta(minutes=duration_minutes)
    window = timedelta(hours=search_hours)
    step = timedelta(minutes=step_minutes)

    before = None
    cursor = proposed_start - step
    while cursor >= proposed_start - window:
        if is_free(merged, cursor, cursor + duration) and cursor + duration <= proposed_start:
            before = (cursor, cursor + duration)
            break
        cursor -= step

    after = None
    cursor = proposed_start + step
    while cursor <= proposed_start + window:
        if is_free(merged, cursor, cursor + duration):
            after = (cursor, cursor + duration)
            break
        cursor += step

    return [slot for slot in (before, after) if slot]


def describe(slot: Block, proposed_start: Optional[datetime] = None) -> dict:
    """The shape the extension renders, matching the existing slot payloads."""
    start, end = slot
    payload = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "formatted_start": start.strftime("%A, %B %d at %I:%M %p").replace(" 0", " "),
        "formatted_time": f"{start.strftime('%I:%M %p').lstrip('0')} - {end.strftime('%I:%M %p').lstrip('0')}",
        "duration_minutes": int((end - start).total_seconds() // 60),
    }
    if proposed_start is not None:
        payload["minutes_from_proposed"] = int((start - proposed_start).total_seconds() // 60)
    return payload


def _round_up(moment: datetime, step_minutes: int) -> datetime:
    remainder = moment.minute % step_minutes
    if remainder == 0 and moment.second == 0 and moment.microsecond == 0:
        return moment
    return (moment + timedelta(minutes=step_minutes - remainder)).replace(second=0, microsecond=0)


def _within_working_hours(
    start: datetime, end: datetime, working_hours: Optional[Tuple[int, int]]
) -> bool:
    if not working_hours:
        return True
    first, last = working_hours
    # Hours from the start of the slot's day, so a closing hour of 24 means
    # midnight (a datetime.time cannot say 24:00).
    day_start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    return day_start + timedelta(hours=first) <= start and end <= day_start + timedelta(hours=last)
