from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz

from backend.models.event_models import ParsedEvent, RecurrenceType
from backend.services.date_parser import DateParser
from backend.services.rules_parser import RuleEvent

from .models import EVAL_FIELDS, EvalEvent

_date_parser = DateParser()


def _empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if _empty(value):
        return None
    return " ".join(str(value).strip().lower().split())


def _recurrence_value(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, RecurrenceType):
        return value.value
    text = str(value).strip().lower()
    if text.startswith("recurrencetype."):
        text = text.split(".", 1)[1]
    return text or "none"


def _to_iso_datetime(value: Optional[str], timezone: str) -> Optional[str]:
    if _empty(value):
        return None

    text = str(value).strip()
    if text.startswith("20") and ("T" in text or " " in text):
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            local_tz = pytz.timezone(timezone)
            if parsed.tzinfo is None:
                parsed = local_tz.localize(parsed)
            else:
                parsed = parsed.astimezone(local_tz)
            return parsed.isoformat()
        except ValueError:
            pass

    local_tz = pytz.timezone(timezone)
    parsed = _date_parser.parse_start_time(text, local_tz)
    return parsed.isoformat() if parsed else text


def normalize_eval_event(event: EvalEvent, timezone: str) -> EvalEvent:
    return EvalEvent(
        title=_normalize_text(event.title),
        start_time=_to_iso_datetime(event.start_time, timezone),
        end_time=_to_iso_datetime(event.end_time, timezone),
        location=_normalize_text(event.location),
        notes=_normalize_text(event.notes),
        recurrence_type=_recurrence_value(event.recurrence_type),
    )


def parsed_event_to_eval_event(event: ParsedEvent, timezone: str) -> EvalEvent:
    end_time = event.end_time
    if _empty(end_time) and event.start_time and event.duration_minutes:
        local_tz = pytz.timezone(timezone)
        start_dt = _date_parser.parse_start_time(event.start_time, local_tz)
        if start_dt:
            end_time = (start_dt + timedelta(minutes=event.duration_minutes)).isoformat()

    return normalize_eval_event(
        EvalEvent(
            title=event.title,
            start_time=event.start_time,
            end_time=end_time,
            location=event.location,
            notes=event.notes,
            recurrence_type=_recurrence_value(event.recurrence_type),
        ),
        timezone,
    )


def rule_event_to_eval_event(event: RuleEvent, timezone: str) -> EvalEvent:
    end_time = event.end
    if _empty(end_time) and event.start and event.duration_minutes:
        local_tz = pytz.timezone(timezone)
        start_dt = _date_parser.parse_start_time(event.start, local_tz)
        if start_dt:
            end_time = (start_dt + timedelta(minutes=event.duration_minutes)).isoformat()

    return normalize_eval_event(
        EvalEvent(
            title=event.title,
            start_time=event.start,
            end_time=end_time,
            location=None,
            notes=None,
            recurrence_type=event.recurrence_type,
        ),
        timezone,
    )


def normalize_event_list(events: List[EvalEvent], timezone: str) -> List[EvalEvent]:
    return [normalize_eval_event(event, timezone) for event in events]


def events_equal(left: List[EvalEvent], right: List[EvalEvent]) -> bool:
    if len(left) != len(right):
        return False

    left_payload = [event.to_dict() for event in left]
    right_payload = [event.to_dict() for event in right]
    return left_payload == right_payload


def field_matches(predicted: Optional[str], expected: Optional[str]) -> bool:
    return predicted == expected
