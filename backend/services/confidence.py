"""Per-field confidence layer for live extractions.

Applies the research findings back to the production platform:

- Every extracted event is checked by the source-grounding verifier
  (backend/evaluation/verifier.py): fields whose values cannot be located in
  the user's input text are marked "ungrounded" so the UI can flag them for
  review before the event is created.
- The rules (Regex) parser is used as a corroboration signal rather than a
  routing mechanism: when the Regex parser independently extracts the same
  value for a field, that field's confidence is upgraded to "corroborated".

One production refinement is layered on top of the frozen research rules: an
end time derived from an explicitly stated duration ("for 2 hours") counts as
grounded, because the duration is evidence the user supplied even though it
is not a clock-time range.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

import pytz
from rapidfuzz import fuzz

from ..evaluation.verifier import GROUNDED, UNGROUNDED, verify_event
from .date_parser import DateParser
from .rules_parser import parse_with_rules

logger = logging.getLogger(__name__)

CORROBORATED = "corroborated"

DURATION_PATTERN = re.compile(
    r"\b(for\s+)?(\d+(\.\d+)?|an?|half\s+an?)\s*(hours?|hrs?|minutes?|mins?)\b",
    re.IGNORECASE,
)

_date_parser = DateParser()


def _times_agree(a: Any, b: Any) -> bool:
    try:
        delta = datetime.fromisoformat(str(a)) - datetime.fromisoformat(str(b))
        return abs(delta.total_seconds()) <= 60
    except (ValueError, TypeError):
        return False


def _resolved_regex_event(source: str, tz_name: str) -> Optional[Dict[str, Any]]:
    """Run the rules parser on the source and resolve its times to ISO."""
    try:
        results = parse_with_rules(source, tz_name)
    except Exception:
        return None
    if not results:
        return None
    rule_event = results[0]
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.UTC

    def resolve(value: Optional[str], allow_end_date: bool = False) -> Optional[str]:
        if not value:
            return None
        parsed = _date_parser.parse_start_time(str(value), tz)
        if not parsed and allow_end_date:
            parsed = _date_parser.parse_end_date(str(value), tz)
        return parsed.isoformat() if parsed else None

    recurrence = getattr(rule_event, "recurrence_type", None)
    return {
        "title": getattr(rule_event, "title", None),
        "start_time": resolve(getattr(rule_event, "start", None)),
        "end_time": resolve(getattr(rule_event, "end", None), allow_end_date=True),
        "recurrence_type": str(recurrence) if recurrence else None,
    }


def attach_confidence(
    event_dict: Dict[str, Any],
    source_text: str,
    tz_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a ``field_confidence`` map to a serialized event dict.

    Values per field: "corroborated" | "grounded" | "ungrounded" | "abstained".
    Failures here must never break the parsing response, so the whole layer is
    guarded and simply omits the map on error.
    """
    try:
        confidence = verify_event(event_dict, source_text)

        if confidence.get("end_time") == UNGROUNDED and DURATION_PATTERN.search(source_text):
            confidence["end_time"] = GROUNDED

        regex_event = _resolved_regex_event(source_text, tz_name or "UTC")
        if regex_event:
            title = event_dict.get("title")
            if (
                confidence.get("title") == GROUNDED
                and title
                and regex_event.get("title")
                and fuzz.ratio(str(title).lower(), str(regex_event["title"]).lower()) >= 85
            ):
                confidence["title"] = CORROBORATED
            for field_name in ("start_time", "end_time"):
                if (
                    confidence.get(field_name) == GROUNDED
                    and event_dict.get(field_name)
                    and regex_event.get(field_name)
                    and _times_agree(event_dict[field_name], regex_event[field_name])
                ):
                    confidence[field_name] = CORROBORATED
            recurrence = event_dict.get("recurrence_type")
            if (
                confidence.get("recurrence_type") == GROUNDED
                and str(recurrence) == str(regex_event.get("recurrence_type"))
            ):
                confidence["recurrence_type"] = CORROBORATED

        event_dict["field_confidence"] = confidence
    except Exception:
        logger.exception("Confidence layer failed; returning event without confidence")
    return event_dict
