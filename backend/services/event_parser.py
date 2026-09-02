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
from .date_parser import DateParser
from .event_expander import EventExpander
from .multiple_event_detector import MultipleEventDetector
from .confidence import duration_minutes_from_source, source_states_end_or_duration

load_dotenv()

logger = logging.getLogger(__name__)

_WEEKDAY = r"monday|tuesday|wednesday|thursday|friday|saturday|sunday"
_NEXT_DURATION = (
    r"(?:for\s+(?:the\s+)?)?next\s+"
    r"(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(months?|weeks?)"
)


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
            start_datetime = self.date_parser.parse_start_time(str(event.start_time), local_tz)
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
            
            logger.info(f"Parsing multiple events from: {text}")
            
            # For multiple events, skip rules parser and go directly to intelligent parser
            # Rules parser is not designed to handle multiple events separated by "and"
            logger.info("Skipping rules parser for multiple events, using intelligent parser")
            
            # Fall back to intelligent parser
            if self.intelligent_parser:
                logger.info("Using intelligent parser with JSON mode")
                events = await self.intelligent_parser.parse(text, str(local_tz))
                logger.info(f"Intelligent parser returned {len(events)} events")
                        
                if events:
                    # If user specified multiple distinct weekdays (e.g., "Saturday and Sunday")
                    # Check if they want recurring or just this weekend/week
                    try:
                        text_lower = text.lower()
                        weekday_names = [
                            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
                        ]
                        mentioned_days = [d for d in weekday_names if f" {d}" in f" {text_lower}"]
                        
                        # Check for recurring indicators (be more specific to avoid false positives)
                        import re
                        has_recurring_indicator = (
                            "every" in text_lower or
                            "each" in text_lower or
                            "weekly" in text_lower or
                            "daily" in text_lower or
                            "monthly" in text_lower or
                            bool(re.search(r'\bfor\s+\d+\s+(weeks?|months?|days?)', text_lower)) or  # "for 4 weeks"
                            bool(re.search(r'\buntil\s+', text_lower))  # "until December"
                        )
                        
                        if len(mentioned_days) >= 2 and len(events) == 1:
                            base_event = events[0]
                            recurrence_str = str(base_event.recurrence_type).lower() if base_event.recurrence_type else "none"
                            
                            # Determine if we should split into separate events per weekday
                            should_split_days = False
                            force_non_recurring = False
                            
                            # If no explicit recurring indicator in text, treat as non-recurring individual events
                            if not has_recurring_indicator:
                                logger.info(f"Multiple weekdays mentioned without recurring indicator - treating as individual events")
                                should_split_days = True
                                force_non_recurring = True
                            # If has recurring indicator AND multiple weekdays, split but keep recurrence
                            elif has_recurring_indicator and recurrence_str in ("weekly", "recurrencetype.weekly"):
                                logger.info(f"Multiple weekdays with recurring indicator - creating recurring events per weekday")
                                should_split_days = True
                                force_non_recurring = False
                            
                            if not should_split_days:
                                # Don't modify the event, let it pass through
                                pass
                            else:
                                # Build a time string from the base event's start time
                                try:
                                    base_dt = datetime.fromisoformat(base_event.start_time) if base_event.start_time and base_event.start_time.startswith('20') else None
                                    if not base_dt:
                                        # Try to parse natural language time
                                        if base_event.start_time:
                                            base_dt = self.date_parser.parse_start_time(base_event.start_time, local_tz)
                                    
                                    if base_dt:
                                        base_dt = base_dt.astimezone(local_tz) if base_dt.tzinfo else local_tz.localize(base_dt)
                                        hour_12 = base_dt.strftime("%I").lstrip("0") or "12"
                                        minute = base_dt.strftime("%M")
                                        ampm = base_dt.strftime("%p").lower()
                                        time_phrase = f"{hour_12}:{minute}{ampm}" if minute != "00" else f"{hour_12}{ampm}"
                                    else:
                                        time_phrase = None
                                except Exception:
                                    time_phrase = None

                                # Determine if we should use "this" or "next" based on the original text
                                text_lower_for_modifier = text.lower()
                                use_next = bool(re.search(r'\bnext\s+(weekend|week|saturday|sunday|monday|tuesday|wednesday|thursday|friday)\b', text_lower_for_modifier))
                                modifier = "next" if use_next else "this"
                                
                                additional_events = []
                                for day in mentioned_days:
                                    # Build a natural phrase like "this sunday at 3pm" or "next saturday at 3pm"
                                    try:
                                        if time_phrase:
                                            phrase = f"{modifier} {day} at {time_phrase}"
                                        else:
                                            phrase = f"{modifier} {day}"
                                        new_start = self.date_parser.parse_start_time(phrase, local_tz)
                                        if new_start:
                                            # Use force_non_recurring flag to determine recurrence settings
                                            cloned = ParsedEvent(
                                                title=base_event.title,
                                                start_time=new_start.isoformat(),
                                                end_time=None,
                                                duration_minutes=base_event.duration_minutes,
                                                location=base_event.location,
                                                notes=base_event.notes,
                                                recurrence_type="none" if force_non_recurring else base_event.recurrence_type,
                                                recurrence_count=None if force_non_recurring else base_event.recurrence_count,
                                                recurrence_interval=1 if force_non_recurring else base_event.recurrence_interval,
                                                end_date=None if force_non_recurring else base_event.end_date,
                                                end_after_count=None,
                                                color=base_event.color,
                                                reminder=base_event.reminder,
                                            )
                                            additional_events.append(cloned)
                                    except Exception:
                                        continue

                                # Replace events with the deduplicated list per mentioned days
                                if additional_events:
                                    # De-duplicate by weekday (keep one per mentioned day)
                                    def weekday_key(ev_dt_iso: str) -> int:
                                        try:
                                            d = datetime.fromisoformat(ev_dt_iso)
                                            d = d.astimezone(local_tz) if d.tzinfo else local_tz.localize(d)
                                            return d.weekday()
                                        except Exception:
                                            return -1

                                    seen = set()
                                    unique_events = []
                                    for ev in additional_events:
                                        key = weekday_key(ev.start_time)
                                        if key not in seen and key != -1:
                                            seen.add(key)
                                            unique_events.append(ev)
                                    if unique_events:
                                        events = unique_events
                                        logger.info(f"Split into {len(events)} {'recurring' if not force_non_recurring else 'individual'} events for mentioned weekdays")
                    except Exception as _e:
                        logger.debug(f"Multi-weekday split skipped: {_e}")

                    # Check if multiple events should be treated as non-recurring
                    # If we have multiple events and no recurring indicators in text, they should all be single events
                    import re
                    text_lower = text.lower()
                    has_recurring_indicator = (
                        "every" in text_lower or
                        "each" in text_lower or
                        "weekly" in text_lower or
                        "daily" in text_lower or
                        "monthly" in text_lower or
                        bool(re.search(r'\bfor\s+\d+\s+(weeks?|months?|days?)', text_lower)) or  # "for 4 weeks"
                        bool(re.search(r'\buntil\s+', text_lower))  # "until December"
                    )
                    
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
                        logger.info(f"Checking event '{event.title}' for recurrence: type={recurrence_str}, count={recurrence_count}")
                        
                        if recurrence_str and recurrence_str != "none" and recurrence_str != "recurrencetype.none":
                            # Keep finite and indefinite series as one calendar RRULE event.
                            # Expanding into many one-offs drops end_date from the UI.
                            logger.info(
                                "Keeping recurring series as one event in multi path: "
                                f"{event.title}, type={recurrence_str}, count={recurrence_count}, "
                                f"end_date={end_date}"
                            )
                            parsed_events.append(event)
                        else:
                            parsed_events.append(event)
                    
                    return parsed_events
                
            # Final fallback
            return await self._fallback_parse_multiple(text)
                
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
            
            # Create a single event as last resort
            now = datetime.now(pytz.timezone('UTC'))
            fallback_event = ParsedEvent(
                title="Event",
                start_time=now.isoformat(),
                end_time=(now + timedelta(hours=1)).isoformat(),
                    duration_minutes=60,
                    location=None,
                    notes=None,
                    recurrence_type="none",
                    recurrence_count=None,
                recurrence_interval=1,
                color=None,
                reminder=None
            )
            
            return [fallback_event]
            
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
                events = await self.intelligent_parser.parse(text, str(local_tz))
                if events and len(events) > 0:
                    event = events[0]
                    event.original_text = text
                    self._resolve_event_datetimes(event, local_tz, source_text=text)
                    
                    return event
            
            # Final fallback - try to extract a better title from the input
            now = datetime.now(local_tz)
            
            # Try to extract a meaningful title from the input
            fallback_title = "Event"
            if text and len(text.strip()) > 0:
                # Remove common time/date words and take the first few words as title
                import re
                cleaned_text = re.sub(r'\b(tomorrow|today|next|this|at|on|for|in|and|the|a|an)\b', '', text.lower())
                words = cleaned_text.split()[:3]  # Take first 3 meaningful words
                if words:
                    fallback_title = ' '.join(words).title()
                    if len(fallback_title) < 2:
                        fallback_title = "Event"
            
            return ParsedEvent(
                title=fallback_title,
                start_time=now.isoformat(),
                end_time=(now + timedelta(hours=1)).isoformat(),
                end_time_assumed=True,
                duration_minutes=60,
                location=None,
                notes=None,
                recurrence_type="none",
                recurrence_count=None,
                recurrence_interval=1,
                color=None,
                reminder=None
            )
            
        except Exception as e:
            logger.error(f"Error parsing event text: {e}")
            now = datetime.now(pytz.timezone('UTC'))
            
            # Try to extract a meaningful title from the input
            fallback_title = "Event"
            if text and len(text.strip()) > 0:
                # Remove common time/date words and take the first few words as title
                import re
                cleaned_text = re.sub(r'\b(tomorrow|today|next|this|at|on|for|in|and|the|a|an)\b', '', text.lower())
                words = cleaned_text.split()[:3]  # Take first 3 meaningful words
                if words:
                    fallback_title = ' '.join(words).title()
                    if len(fallback_title) < 2:
                        fallback_title = "Event"
            
            return ParsedEvent(
                title=fallback_title,
                start_time=now.isoformat(),
                end_time=(now + timedelta(hours=1)).isoformat(),
                end_time_assumed=True,
                duration_minutes=60,
                location=None,
                notes=None,
                recurrence_type="none",
                recurrence_count=None,
                recurrence_interval=1,
                color=None,
                reminder=None
            )
    
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
