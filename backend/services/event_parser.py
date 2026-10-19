"""
Main event parser that orchestrates parsing of natural language event descriptions.
This is the main entry point for event parsing functionality.
"""

import os
import logging
import re
from typing import List, Optional
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv

from ..models.event_models import ParsedEvent
from .intelligent_parser import IntelligentEventParser
from .claude_parser import ClaudeEventParser, DEFAULT_CLAUDE_MODEL
from .rules_parser import parse_with_rules
from .date_checks import check_event_dates
from .weekday_split import says_recurring, split_by_weekday
from .date_parser import DateParser
from .event_expander import EventExpander
from .multiple_event_detector import MultipleEventDetector
from .confidence import duration_minutes_from_source, source_states_end_or_duration
from .log_safety import safe
from .parse_errors import NoEventFound, ParserUnavailable

load_dotenv()

logger = logging.getLogger(__name__)

_WEEKDAY = r"monday|tuesday|wednesday|thursday|friday|saturday|sunday"
_NEXT_DURATION = (
    r"(?:for\s+(?:the\s+)?)?next\s+"
    r"(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(months?|weeks?)"
)


_NEXT_WEEKDAY = re.compile(rf"\bnext\s+({_WEEKDAY})\b", re.IGNORECASE)


def drop_unasked_next(start_time: str, source: str) -> str:
    """Honour "next" only when the user actually wrote it.

    The model tends to answer "every Monday at 9am" with "next Monday at 9am".
    Said on a Thursday that skips the Monday three days away and starts the
    series a week late.
    """
    if not start_time or not source:
        return start_time
    if re.search(r"\bnext\b", source, re.IGNORECASE):
        return start_time
    return _NEXT_WEEKDAY.sub(lambda match: match.group(1), start_time)


def text_implies_recurring_series(text: str) -> bool:
    """True when the input describes a recurring series the rules parser often misses."""
    if not text:
        return False
    lower = text.lower()
    if re.search(r"\b(every|each|daily|weekly|monthly|yearly)\b", lower):
        return True
    if re.search(rf"\b({_WEEKDAY})\b", lower) and re.search(_NEXT_DURATION, lower):
        return True
    return False


class EventParser:
    """Main event parser that orchestrates parsing of natural language event descriptions."""
    
    def __init__(self):
        provider = os.getenv("LLM_PROVIDER", "claude").strip().lower()
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_api_key = openai_api_key

        if provider in ("claude", "anthropic"):
            if anthropic_api_key:
                model = os.getenv("LLM_MODEL", DEFAULT_CLAUDE_MODEL)
                self.intelligent_parser = ClaudeEventParser(anthropic_api_key, model=model)
                logger.info("Live event parser: Claude (%s)", model)
            elif openai_api_key:
                logger.warning(
                    "LLM_PROVIDER is Claude but ANTHROPIC_API_KEY is missing; falling back to OpenAI"
                )
                self.intelligent_parser = IntelligentEventParser(openai_api_key)
            else:
                logger.warning("No LLM API key found. LLM parsing will be disabled.")
                self.intelligent_parser = None
        elif openai_api_key:
            self.intelligent_parser = IntelligentEventParser(openai_api_key)
            logger.info("Live event parser: OpenAI (%s)", self.intelligent_parser.model)
        else:
            logger.warning("OpenAI API key not found. LLM parsing will be disabled.")
            self.intelligent_parser = None
        self.date_parser = DateParser()
        self.event_expander = EventExpander()
        self.multiple_event_detector = MultipleEventDetector()

    def _resolve_event_datetimes(
        self,
        event: ParsedEvent,
        local_tz: pytz.timezone,
        source_text: Optional[str] = None,
    ) -> None:
        """Convert natural-language start/end times to ISO, preserving multi-day ranges."""
        source = source_text or getattr(event, "original_text", None) or ""

        if event.start_time and not str(event.start_time).startswith("20"):
            start_text = drop_unasked_next(str(event.start_time), source)
            start_datetime = self.date_parser.parse_start_time(start_text, local_tz)
            if start_datetime:
                event.start_time = start_datetime.isoformat()

        if event.end_time and not str(event.end_time).startswith("20"):
            end_datetime = self.date_parser.parse_start_time(str(event.end_time), local_tz)
            if not end_datetime:
                end_datetime = self.date_parser.parse_end_date(str(event.end_time), local_tz)
            if end_datetime:
                event.end_time = end_datetime.isoformat()

        if (
            event.start_time
            and str(event.start_time).startswith("20")
            and (not event.end_time or not str(event.end_time).startswith("20"))
        ):
            stated_duration = duration_minutes_from_source(source)
            duration = stated_duration or event.duration_minutes or 60
            if stated_duration:
                event.duration_minutes = stated_duration
            start_dt = datetime.fromisoformat(event.start_time)
            event.end_time = (start_dt + timedelta(minutes=duration)).isoformat()
            # Only label the end as assumed when the user did not state a
            # duration or an end range. "for 2 hours" and "to 8am" are stated.
            event.end_time_assumed = not source_states_end_or_duration(source)

        # A repeat the text never asked for, a time already gone, or a series
        # started at its "until" date: fixed against the user's own words.
        check_event_dates(event, source, datetime.now(local_tz))
    
    async def is_multiple_events(self, text: str) -> bool:
        """Determine if the input text describes multiple events."""
        return await self.multiple_event_detector.is_multiple_events(text)
    
    async def parse_multiple_events(self, text: str, tz_name: Optional[str] = None) -> List[ParsedEvent]:
        """
        Parse multiple events from text.
        """
        try:
            # Get timezone
            if tz_name:
                local_tz = pytz.timezone(tz_name)
            else:
                local_tz = pytz.timezone('UTC')
            
            logger.info(f"Parsing multiple events from: {safe(text)}")
            
            # For multiple events, skip rules parser and go directly to intelligent parser
            # Rules parser is not designed to handle multiple events separated by "and"
            logger.info("Skipping rules parser for multiple events, using intelligent parser")
            
            # Fall back to intelligent parser
            if self.intelligent_parser:
                logger.info("Using intelligent parser with JSON mode")
                events = await self.intelligent_parser.parse(text, str(local_tz), raise_on_failure=True)
                logger.info(f"Intelligent parser returned {len(events)} events")
                        
                if events:
                    # "Gym Mon Wed Fri at 6am": the model often returns only the
                    # first day, so give each listed day its own event.
                    events = split_by_weekday(
                        events,
                        text,
                        local_tz,
                        lambda phrase: self.date_parser.parse_start_time(phrase, local_tz),
                    )

                    # Check if multiple events should be treated as non-recurring
                    # If we have multiple events and no recurring indicators in text, they should all be single events
                    has_recurring_indicator = says_recurring(text)
                    
                    # If we have multiple events without recurring indicators, force them all to be non-recurring
                    if len(events) > 1 and not has_recurring_indicator:
                        logger.info(f"Multiple events detected without recurring indicators - treating all as single events")
                        updated_events = []
                        for event in events:
                            if hasattr(event, 'model_copy'):
                                updated_event = event.model_copy(update={"recurrence_type": "none", "recurrence_count": None})
                            elif hasattr(event, 'copy'):
                                updated_event = event.copy(update={"recurrence_type": "none", "recurrence_count": None})
                            else:
                                # Fallback: modify event in place
                                event.recurrence_type = "none"
                                event.recurrence_count = None
                                updated_event = event
                            updated_events.append(updated_event)
                        events = updated_events
                    
                    # Parse dates and expand recurring events
                    parsed_events = []
                    for event in events:
                        event.original_text = text
                        self._resolve_event_datetimes(event, local_tz, source_text=text)
                        
                        # Check for recurrence and expand if needed
                        recurrence_str = str(event.recurrence_type).lower() if event.recurrence_type else "none"
                        recurrence_count = getattr(event, 'recurrence_count', None)
                        end_date = getattr(event, 'end_date', None)
                        logger.info(f"Checking event {safe(event.title)} for recurrence: type={recurrence_str}, count={recurrence_count}")
                        
                        if recurrence_str and recurrence_str != "none" and recurrence_str != "recurrencetype.none":
                            # Keep finite and indefinite series as one calendar RRULE event.
                            # Expanding into many one-offs drops end_date from the UI.
                            logger.info(
                                "Keeping recurring series as one event in multi path: "
                                f"{safe(event.title)}, type={recurrence_str}, count={recurrence_count}, "
                                f"end_date={end_date}"
                            )
                            parsed_events.append(event)
                        else:
                            parsed_events.append(event)
                    
                    return parsed_events
                
            if not self.intelligent_parser:
                raise ParserUnavailable("no language model is configured")

            # The model found nothing; the rules-based expander may still.
            return await self._fallback_parse_multiple(text)

        except ParserUnavailable:
            raise
        except Exception as e:
            logger.error(f"Error parsing multiple events: {str(e)}")
            return await self._fallback_parse_multiple(text)

    async def _fallback_parse_multiple(self, text: str) -> List[ParsedEvent]:
        """
        Fallback parsing for multiple events when other methods fail.
        """
        try:
            logger.info("Using fallback parsing for multiple events")
            
            # Try simple regex-based expansion
            expanded = self.event_expander.expand_recurring_events(text)
            if expanded:
                return expanded
            
            # Nothing found: the single-event path gets its own try, and reports
            # "no event" rather than this path inventing one at the current time.
            return []

        except Exception as e:
            logger.error(f"Error in fallback parsing: {e}")
            return []

    async def parse_event_text(self, text: str, tz_name: Optional[str] = None) -> ParsedEvent:
        """
        Parse a single event from text.
        """
        try:
            # Get timezone
            if tz_name:
                local_tz = pytz.timezone(tz_name)
            else:
                local_tz = pytz.timezone('UTC')
            
            # Try rules parser first, but skip it when the input clearly describes a
            # recurring series (e.g. "Monday for the next 6 months ... 10pm - 11pm").
            # Rules often match the clock range and return a one-off with no RRULE.
            rules_result = parse_with_rules(text, str(local_tz))
            if rules_result and text_implies_recurring_series(text):
                rule_event = rules_result[0]
                rule_recurrence = (
                    getattr(rule_event, "recurrence_type", None)
                    if not isinstance(rule_event, dict)
                    else rule_event.get("recurrence_type")
                )
                rule_end = (
                    getattr(rule_event, "end_date", None)
                    if not isinstance(rule_event, dict)
                    else rule_event.get("end_date")
                )
                rule_recurrence_str = str(rule_recurrence or "none").lower()
                if rule_recurrence_str in ("", "none") and not rule_end:
                    logger.info(
                        "Skipping rules parser for recurring-series input; using LLM"
                    )
                    rules_result = None
            if rules_result and len(rules_result) > 0:
                event_data = rules_result[0]
                
                # Handle RuleEvent objects (they have attributes, not dictionary keys)
                if hasattr(event_data, 'start'):
                    start_time_str = event_data.start
                    end_time_str = getattr(event_data, 'end', None)
                    title = event_data.title
                    duration_minutes = event_data.duration_minutes or 60
                    recurrence_type = event_data.recurrence_type
                    recurrence_count = event_data.recurrence_count
                    recurrence_interval = event_data.recurrence_interval
                    end_date = event_data.end_date
                    
                    # Don't set default recurrence_count - let normalization handle it
                    # For indefinite recurring events, count should remain None
                    
                    location = getattr(event_data, 'location', None)
                    notes = getattr(event_data, 'notes', None)
                    color = getattr(event_data, 'color', None)
                    reminder = getattr(event_data, 'reminder', None)
                else:
                    # Handle dictionary format (fallback)
                    start_time_str = event_data.get('start_time')
                    end_time_str = event_data.get('end_time') or event_data.get('end')
                    title = event_data.get('title', 'Untitled Event')
                    duration_minutes = event_data.get('duration_minutes', 60)
                    recurrence_type = event_data.get('recurrence_type', 'none')
                    recurrence_count = event_data.get('recurrence_count')
                    recurrence_interval = event_data.get('recurrence_interval', 1)
                    end_date = event_data.get('end_date')
                    
                    # Don't set default recurrence_count - let normalization handle it
                    # For indefinite recurring events, count should remain None
                    
                    location = event_data.get('location')
                    notes = event_data.get('notes')
                    color = event_data.get('color')
                    reminder = event_data.get('reminder')
                
                # Parse start time
                if start_time_str:
                    start_datetime = self.date_parser.parse_start_time(start_time_str, local_tz)
                    if start_datetime:
                        end_datetime = None
                        if end_time_str:
                            end_datetime = self.date_parser.parse_start_time(end_time_str, local_tz)
                            if not end_datetime:
                                end_datetime = self.date_parser.parse_end_date(end_time_str, local_tz)
                        if end_datetime:
                            end_assumed = False
                        else:
                            stated_duration = duration_minutes_from_source(text)
                            if stated_duration:
                                duration_minutes = stated_duration
                            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
                            end_assumed = not source_states_end_or_duration(text)

                        return ParsedEvent(
                            title=title,
                            start_time=start_datetime.isoformat(),
                            end_time=end_datetime.isoformat(),
                            end_time_assumed=end_assumed,
                            duration_minutes=duration_minutes,
                            location=location,
                            notes=notes,
                            recurrence_type=recurrence_type,
                            recurrence_count=recurrence_count,
                            recurrence_interval=recurrence_interval,
                            end_date=end_date,
                            end_after_count=None,
                            color=color,
                            reminder=reminder
                        )
            
            # Fall back to intelligent parser
            if self.intelligent_parser:
                events = await self.intelligent_parser.parse(text, str(local_tz), raise_on_failure=True)
                if events and len(events) > 0:
                    event = events[0]
                    event.original_text = text
                    self._resolve_event_datetimes(event, local_tz, source_text=text)
                    
                    return event
            
            if not self.intelligent_parser:
                raise ParserUnavailable("no language model is configured")
            raise NoEventFound()

        except (ParserUnavailable, NoEventFound):
            raise
        except Exception as e:
            logger.error(f"Error parsing event text: {e}")
            raise

    async def expand_recurring_events(self, text: str, tz_name: Optional[str] = None) -> List[ParsedEvent]:
        """
        Expand recurring events from text.
        """
        return await self.event_expander.expand_single_recurring_event(
            ParsedEvent(
                title="Event",
                start_time=text,
                end_time=None,
                    duration_minutes=60,
                location=None,
                notes=None,
                recurrence_type="daily",
                    recurrence_count=None,
                recurrence_interval=1,
                color=None,
                reminder=None
            ),
            tz_name,
            text
        )
