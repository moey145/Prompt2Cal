"""Deterministic rule-based event parsing for Prompt2Cal.

This module handles common patterns without relying on the LLM so we can
guarantee correct behaviour for straightforward inputs.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

import dateparser
import pytz


@dataclass
class RuleEvent:
    """Intermediate event object produced by the rules parser."""

    title: str
    start: str
    end: Optional[str] = None
    duration_minutes: Optional[int] = None
    recurrence_type: str = "none"
    recurrence_interval: int = 1
    recurrence_count: Optional[int] = None
    end_date: Optional[str] = None


class RulesParser:
    """Deterministic parsing layer to handle common patterns."""

    def __init__(self, timezone: str = "UTC") -> None:
        try:
            self.tz = pytz.timezone(timezone)
        except Exception:
            self.tz = pytz.UTC

    def parse(self, text: str) -> List[RuleEvent]:
        text = text.strip()
        handlers = [
            self._parse_range_with_relative_day,
            self._parse_bulk_range,
            self._parse_ordinal_monthly,
            self._parse_range_without_day,
            self._parse_single_relative,
        ]

        for handler in handlers:
            events = handler(text)
            if events:
                return events
        return []

    # --------------------------- handlers ---------------------------

    def _parse_range_with_relative_day(self, text: str) -> List[RuleEvent]:
        pattern = re.compile(
            r"^(?P<title>.+?)\s+at\s+(?P<start>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*-\s*(?P<end>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+(?P<day>tomorrow|today)$",
            re.IGNORECASE,
        )
        match = pattern.match(text)
        if not match:
            return []

        title = match.group("title").strip().rstrip(",")
        start_time = f"{match.group('day')} at {match.group('start')}"
        end_time = f"{match.group('day')} at {match.group('end')}"
        duration = self._duration_minutes(start_time, end_time)
        return [
            RuleEvent(
                title=title,
                start=start_time,
                end=end_time,
                duration_minutes=duration,
            )
        ]

    def _parse_bulk_range(self, text: str) -> List[RuleEvent]:
        pattern = re.compile(
            r"^(?P<title>.+?)\s+at\s+(?P<start>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*-\s*(?P<end>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+from\s+(?P<start_day>today|tomorrow)\s*(?:-|to|through)\s*(?P<end_day>\w+)$",
            re.IGNORECASE,
        )
        match = pattern.match(text)
        if not match:
            return []

        title = match.group("title").strip().rstrip(",")
        start_time = match.group("start")
        end_time = match.group("end")
        start_day = match.group("start_day").lower()
        end_day = match.group("end_day").lower()

        start_literal = f"{start_day} at {start_time}"
        end_literal = f"{start_day} at {end_time}"
        duration = self._duration_minutes(start_literal, end_literal)

        end_date = self._resolve_weekday(end_day, inclusive=True)
        return [
            RuleEvent(
                title=title,
                start=start_literal,
                end=end_literal,
                duration_minutes=duration,
                recurrence_type="daily",
                recurrence_interval=1,
                end_date=end_date,
            )
        ]

    def _parse_ordinal_monthly(self, text: str) -> List[RuleEvent]:
        # Pattern: "First Monday of each month board meeting at 9am"
        alternate_pattern = re.compile(
            r"^(?P<ordinal>first|second|third|fourth|last)\s+(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
            r"\s+of\s+each\s+month\s+(?P<title>.+?)\s+at\s+(?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)$",
            re.IGNORECASE,
        )

        match = alternate_pattern.match(text)
        if not match:
            return []

        title = match.group("title").strip().rstrip(",")
        ordinal = match.group("ordinal").lower()
        weekday = match.group("weekday").lower()
        time_str = match.group("time")

        next_occurrence = self._next_ordinal_weekday(ordinal, weekday, time_str)
        if not next_occurrence:
            return []

        start_iso = next_occurrence.isoformat()
        duration = 60
        return [
            RuleEvent(
                title=title,
                start=start_iso,
                end=None,
                duration_minutes=duration,
                recurrence_type="monthly",
                recurrence_interval=1,
            )
        ]

    def _parse_range_without_day(self, text: str) -> List[RuleEvent]:
        pattern = re.compile(
            r"^(?P<title>.+?)\s+at\s+(?P<start>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*-\s*(?P<end>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)$",
            re.IGNORECASE,
        )
        match = pattern.match(text)
        if not match:
            return []

        title = match.group("title").strip().rstrip(",")
        start_time = match.group("start")
        end_time = match.group("end")
        now = datetime.now(self.tz)
        start_literal = (
            f"today at {start_time}"
            if now.strftime("%H:%M") <= self._to_24h(start_time)
            else f"tomorrow at {start_time}"
        )
        end_literal = start_literal.replace(start_time, end_time)
        duration = self._duration_minutes(start_literal, end_literal)
        return [
            RuleEvent(
                title=title,
                start=start_literal,
                end=end_literal,
                duration_minutes=duration,
            )
        ]

    def _parse_single_relative(self, text: str) -> List[RuleEvent]:
        pattern = re.compile(
            r"^(?P<title>.+?)\s+(?P<relative>in\s+\d+\s+(?:minutes?|hours?|days?)|tomorrow|today)$",
            re.IGNORECASE,
        )
        match = pattern.match(text)
        if not match:
            return []

        title = match.group("title").strip().rstrip(",")
        rel = match.group("relative")

        # Extract time from the title if present (e.g., "Meeting 7pm tomorrow")
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", title, re.IGNORECASE)
        start_literal = rel
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2) if time_match.group(2) else ""
            ampm = time_match.group(3)
            time_str = f"{hour}{':' + minute if minute else ''}{ampm}"
            start_literal = f"{rel} at {time_str}"
            # Remove the time portion from the title to avoid duplication
            title = re.sub(r"\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)\s*", " ", title, flags=re.IGNORECASE).strip()

        return [
            RuleEvent(
                title=title,
                start=start_literal,
                duration_minutes=60,
            )
        ]

    # --------------------------- helpers ----------------------------

    def _duration_minutes(self, start_str: str, end_str: str) -> int:
        settings = {
            "TIMEZONE": str(self.tz),
            "RETURN_AS_TIMEZONE_AWARE": True,
        }
        start_dt = dateparser.parse(start_str, settings=settings)
        end_dt = dateparser.parse(end_str, settings=settings)
        if not start_dt or not end_dt:
            return 60
        delta = max(end_dt - start_dt, timedelta(minutes=1))
        return int(delta.total_seconds() // 60)

    def _next_ordinal_weekday(self, ordinal: str, weekday: str, time_str: str) -> Optional[datetime]:
        now = datetime.now(self.tz)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        candidate = self._nth_weekday_in_month(start_of_month, ordinal, weekday, time_str)
        if candidate and candidate > now:
            return candidate

        next_month = (start_of_month.month % 12) + 1
        next_year = start_of_month.year + (1 if next_month == 1 else 0)
        start_of_next_month = start_of_month.replace(year=next_year, month=next_month)
        return self._nth_weekday_in_month(start_of_next_month, ordinal, weekday, time_str)

    def _nth_weekday_in_month(self, base: datetime, ordinal: str, weekday: str, time_str: str) -> Optional[datetime]:
        weekday_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        target_weekday = weekday_map[weekday]
        hour, minute = self._parse_time(time_str)

        first_weekday, days_in_month = calendar.monthrange(base.year, base.month)

        if ordinal == "last":
            last_day = self.tz.localize(datetime(base.year, base.month, days_in_month, hour, minute))
            delta = (last_day.weekday() - target_weekday) % 7
            return last_day - timedelta(days=delta)

        ordinal_map = {"first": 0, "second": 1, "third": 2, "fourth": 3}
        if ordinal not in ordinal_map:
            return None

        first_occurrence_day = 1 + (target_weekday - first_weekday) % 7
        day = first_occurrence_day + ordinal_map[ordinal] * 7
        if day > days_in_month:
            day -= 7
        naive = datetime(base.year, base.month, day, hour, minute)
        return self.tz.localize(naive)

    def _parse_time(self, time_str: str) -> tuple[int, int]:
        match = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", time_str, re.IGNORECASE)
        if not match:
            return 9, 0
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)
        if ampm:
            ampm = ampm.lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
        return hour, minute

    def _to_24h(self, time_str: str) -> str:
        hour, minute = self._parse_time(time_str)
        return f"{hour:02d}:{minute:02d}"

    def _resolve_weekday(self, keyword: str, inclusive: bool = False) -> Optional[str]:
        days_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        keyword = keyword.lower()
        now = datetime.now(self.tz)
        if keyword in ("today", "tomorrow"):
            delta = 0 if keyword == "today" else 1
            end = now + timedelta(days=delta)
            return end.date().isoformat()
        if keyword not in days_map:
            return None
        target = days_map[keyword]
        current = now.weekday()
        delta = (target - current) % 7
        if delta == 0 and not inclusive:
            delta = 7
        end = now + timedelta(days=delta)
        return end.date().isoformat()


def parse_with_rules(text: str, timezone: str = "UTC") -> List[RuleEvent]:
    return RulesParser(timezone).parse(text)


