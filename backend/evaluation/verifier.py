"""Source-grounding verifier for extracted event fields.

For each non-null field an extractor produced, check whether the value is
locatable in (grounded by) the original input text. Fields with no supporting
evidence in the source are flagged as ungrounded, i.e. candidate
hallucinations.

GROUNDING RULES (frozen before scoring, analogous to ground-truth labelling):

1. title: grounded if at least half of the title's content words (length > 2)
   appear in the source under fuzzy matching (partial ratio >= 85).
2. start_time: grounded if the source contains ANY explicit date signal
   (weekday, month, relative day such as "tomorrow" or "next week") OR any
   explicit clock-time signal. Rationale: the schema packs date and time into
   start_time, and ground truth labels day-only starts as legitimate.
3. end_time: grounded only if the source contains explicit range or end
   evidence: two or more clock-time signals, a "from ... to/until/till"
   construction, a standalone "until/till", or a dash adjacent to a digit or
   am/pm marker. A single start time does NOT ground an end time; this is
   exactly the "default one hour end time" fabrication pattern.
4. location: grounded if the value fuzzy-matches the source
   (partial ratio >= 80).
5. notes: same rule as location.
6. recurrence_type: "none" or null is abstention and always grounded;
   any other value requires an explicit recurrence keyword in the source.

Deliberate design decisions, mirroring the benchmark labelling rules:
- A weekday alone does NOT ground a clock time.
- Vague approximations such as "7ish" do NOT ground a precise clock time.
- Spelled-out times ("eight thirty aye em") DO ground a time, because the
  voice-to-text category transcribes clock times as words by design.
- dateparser's search_dates is not used: its REQUIRE_PARTS setting cannot
  require a time component, which is the distinction this verifier exists
  to draw.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

from rapidfuzz import fuzz

# Clock-time signals: digital times, am/pm forms, named times of day,
# o'clock, and spelled-out times with am/pm transcription variants.
TIME_PATTERN = re.compile(
    r"\b(\d{1,2}[:.]\d{2}"
    r"|\d{1,2}\s*(am|pm|a\.m\.?|p\.m\.?)"
    r"|noon|midday|midnight|morning|afternoon|evening|tonight"
    r"|o'?clock)\b",
    re.IGNORECASE,
)

SPELLED_TIME_PATTERN = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b"
    r"[\s\w]{0,12}?"
    r"\b(thirty|fifteen|forty[\s-]?five|o'?clock|(aye|ay|a)\s*(em|m)|(pee|p)\s*(em|m))\b",
    re.IGNORECASE,
)

DATE_PATTERN = re.compile(
    r"\b(mon|tues?|wed(nes)?|thur?s?|fri|sat(ur)?|sun)(day)?\b"
    r"|\b(jan(uary)?|feb(ruary)?|mar(ch)?|apr(il)?|may|jun(e)?|jul(y)?"
    r"|aug(ust)?|sep(tember)?|oct(ober)?|nov(ember)?|dec(ember)?)\b"
    r"|\b(today|tomorrow|tonight|weekend)\b"
    r"|\b(next|this|coming)\s+(week|month|year)\b"
    r"|\b\d{1,2}(st|nd|rd|th)\b",
    re.IGNORECASE,
)

RANGE_WORD_PATTERN = re.compile(
    r"\bfrom\b.+\b(to|until|till|through)\b|\b(until|till)\b",
    re.IGNORECASE | re.DOTALL,
)

RANGE_DASH_PATTERN = re.compile(r"(\d|am|pm)\s*[-\u2013]\s*\d", re.IGNORECASE)

RECURRENCE_KEYWORDS = re.compile(
    r"\b(every|daily|weekly|monthly|yearly|annually|each|recurring|weekdays)\b",
    re.IGNORECASE,
)


def _has_time_signal(source: str) -> bool:
    return bool(TIME_PATTERN.search(source)) or bool(SPELLED_TIME_PATTERN.search(source))


def _has_date_signal(source: str) -> bool:
    return bool(DATE_PATTERN.search(source))


def ground_title(value: str, source: str) -> bool:
    tokens = [t for t in re.findall(r"\w+", value.lower()) if len(t) > 2]
    if not tokens:
        return False
    source_lower = source.lower()
    hits = sum(1 for t in tokens if fuzz.partial_ratio(t, source_lower) >= 85)
    return hits / len(tokens) >= 0.5


def ground_start_time(value: str, source: str) -> bool:
    return _has_date_signal(source) or _has_time_signal(source)


def ground_end_time(value: str, source: str) -> bool:
    time_signals = len(TIME_PATTERN.findall(source)) + len(
        SPELLED_TIME_PATTERN.findall(source)
    )
    if time_signals >= 2:
        return True
    if RANGE_WORD_PATTERN.search(source):
        return True
    if RANGE_DASH_PATTERN.search(source):
        return True
    return False


def ground_location(value: str, source: str) -> bool:
    return fuzz.partial_ratio(value.lower(), source.lower()) >= 80


def ground_notes(value: str, source: str) -> bool:
    return fuzz.partial_ratio(value.lower(), source.lower()) >= 80


def ground_recurrence(value: Optional[str], source: str) -> bool:
    if value in (None, "", "none"):
        return True
    return bool(RECURRENCE_KEYWORDS.search(source))


_FIELD_CHECKS = {
    "title": ground_title,
    "start_time": ground_start_time,
    "end_time": ground_end_time,
    "location": ground_location,
    "notes": ground_notes,
    "recurrence_type": ground_recurrence,
}

ABSTAINED = "abstained"
GROUNDED = "grounded"
UNGROUNDED = "ungrounded"


def verify_event(event: Dict[str, Optional[str]], source: str) -> Dict[str, str]:
    """Return {field: 'abstained' | 'grounded' | 'ungrounded'} per field.

    ``event`` is a dict with the six evaluation fields; values may be None.
    A null value (or recurrence 'none') is abstention and is never flagged.
    """
    result: Dict[str, str] = {}
    for field_name, check in _FIELD_CHECKS.items():
        value = event.get(field_name)
        if field_name == "recurrence_type":
            if value in (None, "", "none"):
                result[field_name] = ABSTAINED
            else:
                result[field_name] = GROUNDED if check(value, source) else UNGROUNDED
            continue
        if value in (None, ""):
            result[field_name] = ABSTAINED
        else:
            result[field_name] = GROUNDED if check(value, source) else UNGROUNDED
    return result
