"""
Intelligent Event Parser using LLM with structured JSON output.
This replaces hardcoded regex patterns with AI-powered parsing.
"""

import json
import logging
import re
import time
import hashlib
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
import openai
from ..models.event_models import ParsedEvent, RecurrenceType

logger = logging.getLogger(__name__)

# Cache for parsed events (v18 - fix start_time for recurring events to not include "every day" in time string)
_cache = {}
MAX_CACHE_SIZE = 100
CACHE_VERSION = "v30"  # v30: weekday + for-the-next-N-months stays a single recurring series with end_date

# GPT-5 rejects non-default temperature values; omit the parameter and rely on
# repeated-run consistency measurement instead.
DEFAULT_MODEL = "gpt-5"
MODELS_WITHOUT_TEMPERATURE = frozenset({"gpt-5"})


class IntelligentEventParser:
    """
    Uses OpenAI's JSON mode to parse natural language into structured event data.
    This eliminates the need for hardcoded regex patterns.
    """
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = DEFAULT_MODEL
        self._setup_common()

    def _setup_common(self):
        """Provider-agnostic setup shared by all parser subclasses."""
        self.success_count = 0
        self.failure_count = 0
        self.json_schema = {
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "start_time": {"type": "string"},
                            "end_time": {"type": ["string", "null"]},
                            "duration_minutes": {"type": "integer"},
                            "location": {"type": ["string", "null"]},
                            "notes": {"type": ["string", "null"]},
                            "color": {"type": ["string", "null"]},
                            "reminder": {"type": ["string", "null"]},
                            "recurrence_type": {"type": "string", "enum": ["none", "daily", "weekly", "monthly", "yearly"]},
                            "recurrence_count": {"type": ["integer", "null"]},
                            "recurrence_interval": {"type": "integer"},
                            "recurrence_days": {"type": ["array", "null"], "items": {"type": "string"}},
                            "buffer_before": {"type": "integer"},
                            "buffer_after": {"type": "integer"},
                            "end_date": {"type": ["string", "null"]},
                            "end_after_count": {"type": ["integer", "null"]},
                            "skip_dates": {"type": ["array", "null"], "items": {"type": "string"}}
                        },
                        "required": ["title", "start_time", "duration_minutes"]
                    }
                }
            },
            "required": ["events"]
        }
    
    async def parse(
        self,
        text: str,
        timezone: str = "UTC",
        *,
        use_cache: bool = True,
        temperature: float = 0.0,
    ) -> List[ParsedEvent]:
        """
        Parse natural language event description into structured events with reliability features.
        
        Examples:
        - "Lunch with Sarah next Tuesday at 1pm"
        - "Every Monday workshop at 9am for 3 hours for 4 weeks"
        - "Every sunday strategy meeting at 9am -11am for 8 weeks at Greenacre gym"
        - "Every other Tuesday mentoring session at 5pm for 2 months"
        """
        parse_start_time = time.time()
        
        try:
            # Sanitize input
            sanitized = self._sanitize_input(text)
            
            # Check cache
            cache_key = self._get_cache_key(sanitized)
            logger.debug(f"Cache key: {cache_key} (version: {CACHE_VERSION})")
            if use_cache and cache_key in _cache:
                logger.info(f"Cache hit for: {sanitized[:50]}... (key: {cache_key})")
                cached_result = _cache[cache_key]
                # Re-normalize cached results to ensure indefinite recurring events are handled correctly
                # This is important because cache might have been populated before normalization fixes
                normalized_result = []
                for cached_event in cached_result:
                    # Apply post-processing to extract time from title if missing from start_time
                    normalized_event = self._apply_time_extraction_post_processing(cached_event, sanitized)
                    normalized_event = self._normalize_recurrence(normalized_event, sanitized)
                    normalized_result.append(normalized_event)
                self.success_count += 1
                return normalized_result
            else:
                logger.debug(f"Cache miss for: {sanitized[:50]}... (key: {cache_key})")
            
            # Parse with LLM
            prompt = self._build_prompt(sanitized, timezone)

            raw_content = self._call_llm(self._get_system_prompt(), prompt, temperature)

            result = json.loads(raw_content)
            events = result.get("events", [])
            
            logger.info(f"Intelligent parser found {len(events)} events from: '{sanitized}'")
            
            # Convert to ParsedEvent objects
            parsed_events = []
            for event_data in events:
                # Log what LLM returned for debugging
                logger.info(f"LLM returned - title: '{event_data.get('title')}', start_time: '{event_data.get('start_time')}'")
                # Convert recurrence_type string to enum
                recurrence_str = event_data.get("recurrence_type", "none")
                recurrence_enum = RecurrenceType(recurrence_str) if recurrence_str else RecurrenceType.NONE
                
                # Handle empty title from LLM
                title = event_data.get("title", "Untitled Event")
                if not title or title.strip() == "":
                    title = "Untitled Event"
                
                # Ensure duration is never 0 or negative
                duration = event_data.get("duration_minutes", 60)
                if not duration or duration < 5:
                    duration = 60
                
                start_time = event_data.get("start_time")
                
                # Create a temporary ParsedEvent to apply post-processing
                temp_event = ParsedEvent(
                    title=title,
                    start_time=start_time,
                    end_time=event_data.get("end_time"),
                    duration_minutes=duration,
                    location=event_data.get("location"),
                    notes=event_data.get("notes"),
                    recurrence_type=recurrence_enum,
                    recurrence_count=event_data.get("recurrence_count"),
                    recurrence_interval=event_data.get("recurrence_interval", 1),
                    buffer_before=event_data.get("buffer_before", 0),
                    buffer_after=event_data.get("buffer_after", 0),
                    end_date=event_data.get("end_date"),
                    end_after_count=event_data.get("end_after_count"),
                    color=event_data.get("color"),
                    reminder=event_data.get("reminder")
                )
                
                # Apply post-processing to extract time from title if missing from start_time
                temp_event = self._apply_time_extraction_post_processing(temp_event, sanitized)
                
                parsed_event = ParsedEvent(
                    title=temp_event.title,
                    start_time=temp_event.start_time,
                    end_time=event_data.get("end_time"),
                    duration_minutes=duration,
                    location=event_data.get("location"),
                    notes=event_data.get("notes"),
                    recurrence_type=recurrence_enum,
                    recurrence_count=event_data.get("recurrence_count"),
                    recurrence_interval=event_data.get("recurrence_interval", 1),
                    buffer_before=event_data.get("buffer_before", 0),
                    buffer_after=event_data.get("buffer_after", 0),
                    end_date=event_data.get("end_date"),
                    end_after_count=event_data.get("end_after_count"),
                    color=event_data.get("color"),
                    reminder=event_data.get("reminder")
                )

                # Normalize recurrence information
                parsed_event = self._normalize_recurrence(parsed_event, sanitized)
                parsed_events.append(parsed_event)
            
            # Validate events
            if not self._validate_events(parsed_events):
                logger.error("Validation failed for parsed events")
                self.failure_count += 1
                return []
            
            # Cache successful results
            if use_cache and len(_cache) >= MAX_CACHE_SIZE:
                _cache.pop(next(iter(_cache)))
            if use_cache:
                _cache[cache_key] = parsed_events
            
            duration = time.time() - parse_start_time
            logger.info(f"Parse successful in {duration:.2f}s: {len(parsed_events)} events")
            self.success_count += 1
            
            return parsed_events
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            self.failure_count += 1
            return []
        except openai.RateLimitError:
            logger.error("Rate limit exceeded")
            self.failure_count += 1
            return []
        except openai.APITimeoutError:
            logger.error("API timeout")
            self.failure_count += 1
            return []
        except Exception as e:
            logger.error(f"Error in intelligent parsing: {str(e)}")
            self.failure_count += 1
            return []
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        """Call the LLM and return the raw JSON string content.

        Override this in a subclass to target a different provider while
        reusing the shared prompt building and post-processing pipeline.
        """
        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        if self.model not in MODELS_WITHOUT_TEMPERATURE:
            request_kwargs["temperature"] = temperature

        response = self.client.chat.completions.create(**request_kwargs)
        return response.choices[0].message.content

    def _sanitize_input(self, text: str) -> str:
        """Clean input before parsing."""
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Normalize time formats
        text = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 - \2', text)
        
        # Fix common typos
        text = text.replace("tomorow", "tomorrow")
        text = text.replace("nex ", "next ")
        
        # Limit length
        if len(text) > 500:
            logger.warning(f"Input too long, truncating: {len(text)} chars")
            text = text[:500]
        
        return text.strip()

    def _apply_time_extraction_post_processing(self, event: ParsedEvent, original_text: str) -> ParsedEvent:
        """
        Post-processing: Extract time from title or original text if missing from start_time.
        This handles cases like "Meeting 7pm tomorrow" where LLM might put "7pm" in title.
        """
        if not event.start_time:
            return event
        
        # Check if start_time already has a time
        if re.search(r'\d{1,2}\s*([ap]m|:\d{2})', event.start_time.lower()):
            return event  # Time already present, no need to extract
        
        # Check if time is in title
        title_lower = event.title.lower() if event.title else ""
        time_in_title = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap]m)', title_lower)
        if time_in_title:
            hour = time_in_title.group(1)
            minute = time_in_title.group(2) if time_in_title.group(2) else ""
            ampm = time_in_title.group(3)
            time_str = f"{hour}{':' + minute if minute else ''}{ampm}"
            new_start_time = f"{event.start_time} at {time_str}"
            # Remove time from title
            new_title = re.sub(r'\s*\d{1,2}(?::\d{2})?\s*[ap]m\s*', ' ', event.title, flags=re.IGNORECASE).strip()
            logger.info(f"Extracted time from title: '{time_str}', updated start_time to: '{new_start_time}', cleaned title to: '{new_title}'")
            
            # Create updated event
            if hasattr(event, 'model_copy'):
                return event.model_copy(update={"start_time": new_start_time, "title": new_title})
            else:
                event_dict = event.dict() if hasattr(event, 'dict') else event.__dict__.copy()
                event_dict["start_time"] = new_start_time
                event_dict["title"] = new_title
                return ParsedEvent(**event_dict)
        
        # Also check original text if time still not found
        text_lower = original_text.lower()
        time_in_text = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap]m)', text_lower)
        if time_in_text:
            hour = time_in_text.group(1)
            minute = time_in_text.group(2) if time_in_text.group(2) else ""
            ampm = time_in_text.group(3)
            time_str = f"{hour}{':' + minute if minute else ''}{ampm}"
            new_start_time = f"{event.start_time} at {time_str}"
            logger.info(f"Extracted time from original text: '{time_str}', updated start_time to: '{new_start_time}'")
            
            # Create updated event
            if hasattr(event, 'model_copy'):
                return event.model_copy(update={"start_time": new_start_time})
            else:
                event_dict = event.dict() if hasattr(event, 'dict') else event.__dict__.copy()
                event_dict["start_time"] = new_start_time
                return ParsedEvent(**event_dict)
        
        return event

    def _normalize_recurrence(self, event: ParsedEvent, original_text: str = "") -> ParsedEvent:
        """Normalize recurrence info returned by LLM."""
        try:
            import re
            import dateparser

            # Get recurrence type as string value
            recurrence_type = event.recurrence_type.value if isinstance(event.recurrence_type, RecurrenceType) else str(event.recurrence_type or "none").lower()

            # Check for quarterly patterns and convert to monthly with interval=3
            text_lower_for_quarter = original_text.lower()
            has_quarterly = bool(re.search(r'\b(every|each)\s+quarter\b', text_lower_for_quarter))
            if has_quarterly:
                # Convert quarterly to monthly with interval=3
                recurrence_type = "monthly"
                logger.info(f"Detected quarterly pattern, converting to monthly with interval=3: '{original_text}'")

            # Derive recurrence_type from notes if missing
            if recurrence_type == "none" and event.notes:
                notes_lower = event.notes.lower()
                if "every" in notes_lower or "weekly" in notes_lower:
                    recurrence_type = "weekly"
                elif "daily" in notes_lower or "each day" in notes_lower:
                    recurrence_type = "daily"
                elif "monthly" in notes_lower or "each month" in notes_lower:
                    recurrence_type = "monthly"

            # Normalize duration phrases like "next two months"
            recurrence_count = event.recurrence_count
            text_lower_src = (original_text or "").lower()
            weekday_in_text = re.search(
                r"\b(every\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
                text_lower_src,
            )
            next_duration = re.search(
                r"\b(?:for\s+(?:the\s+)?)?next\s+(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+(months?|weeks?)\b",
                text_lower_src,
            )
            # "Monday for the next 6 months" is a weekly series even without "every"
            if (
                weekday_in_text
                and next_duration
                and recurrence_type in (None, "", "none")
            ):
                recurrence_type = "weekly"
                logger.info(
                    "Inferred weekly recurrence from weekday + next-N duration: '%s'",
                    original_text,
                )

            if (recurrence_type in {"weekly", "daily", "monthly"} and
                    (recurrence_count is None or recurrence_count <= 0 or not event.end_date)):

                # Include original input text to catch patterns like "for 6 weeks", "for the next 3 months", "for next 3 months"
                source_text = f"{original_text} {event.notes or ''} {event.title} {event.start_time}".lower()
                duration_match = re.search(r'(for\s+(?:the\s+)?(?:next\s+)?|next\s+)?(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+(weeks?|months?|days?)', source_text)
                if duration_match:
                    number_word = duration_match.group(2)
                    unit = duration_match.group(3)

                    word_to_number = {
                        'two': 2,
                        'three': 3,
                        'four': 4,
                        'five': 5,
                        'six': 6,
                        'seven': 7,
                        'eight': 8,
                        'nine': 9,
                        'ten': 10
                    }

                    try:
                        count_value = int(number_word)
                    except ValueError:
                        count_value = word_to_number.get(number_word, None)

                    if count_value:
                        if 'week' in unit:
                            recurrence_count = count_value
                            recurrence_type = 'weekly'
                        elif 'month' in unit:
                            # Prefer an end_date for "next N months" so the calendar
                            # gets UNTIL rather than an approximate weekly COUNT.
                            recurrence_type = 'weekly'
                            if not event.end_date:
                                try:
                                    start_dt = dateparser.parse(str(event.start_time)) or datetime.now()
                                    month = start_dt.month - 1 + count_value
                                    year = start_dt.year + month // 12
                                    month = month % 12 + 1
                                    day = min(start_dt.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
                                    end_dt = start_dt.replace(year=year, month=month, day=day)
                                    event = event.model_copy(update={"end_date": end_dt.strftime("%Y-%m-%d")}) if hasattr(event, "model_copy") else event.copy(update={"end_date": end_dt.strftime("%Y-%m-%d")})
                                    logger.info(
                                        "Set end_date from next-%s-months phrase: %s",
                                        count_value,
                                        event.end_date,
                                    )
                                except Exception as end_err:
                                    logger.warning("Failed to derive end_date from months phrase: %s", end_err)
                                    recurrence_count = count_value * 4
                            # Keep count None when end_date is set; RRULE uses UNTIL
                            if event.end_date:
                                recurrence_count = None
                        elif 'day' in unit:
                            recurrence_count = count_value
                            recurrence_type = 'daily'

            # Estimate recurrence_count from end_date if provided
            if event.end_date and recurrence_count in (None, 0):
                try:
                    start_dt = dateparser.parse(event.start_time)
                    end_dt = dateparser.parse(event.end_date)
                    if start_dt and end_dt and end_dt > start_dt:
                        delta_days = (end_dt - start_dt).days
                        if recurrence_type == 'weekly':
                            recurrence_count = max(1, delta_days // 7)
                        elif recurrence_type == 'daily':
                            recurrence_count = max(1, delta_days)
                        elif recurrence_type == 'monthly':
                            recurrence_count = max(1, delta_days // 30)
                except Exception as e:
                    logger.warning(f"Failed to infer recurrence_count from end_date: {e}")

            # For "next N months" phrases, end_date is the source of truth.
            # Drop approximate COUNT so the calendar RRULE uses UNTIL only.
            if event.end_date and next_duration and "month" in next_duration.group(2):
                recurrence_count = None
                if recurrence_type in (None, "", "none"):
                    recurrence_type = "weekly"

            # Ensure valid recurrence_interval
            # If quarterly pattern detected, set interval to 3
            if has_quarterly:
                recurrence_interval = 3
            else:
                recurrence_interval = event.recurrence_interval or 1

            # Convert recurrence_type back to enum
            recurrence_enum = RecurrenceType(recurrence_type) if recurrence_type else RecurrenceType.NONE

            # Log for debugging
            logger.info(f"Before indefinite check: recurrence_enum={recurrence_enum}, recurrence_count={recurrence_count}, end_date={event.end_date}, original_text='{original_text}'")

            # First, check for quarterly patterns and adjust start_time if needed
            # Then check for month range patterns and adjust start_time if needed
            # This should run regardless of whether end_date is set or not
            try:
                text_lower_check = original_text.lower()
                
                # Check for quarterly patterns (e.g., "first Monday of every quarter")
                has_quarterly_check = bool(re.search(r'\b(every|each)\s+quarter\b', text_lower_check))
                if has_quarterly_check and recurrence_enum != RecurrenceType.NONE:
                    logger.info(f"Quarterly pattern detected, adjusting start_time: '{original_text}'")
                    import dateparser
                    import calendar
                    from datetime import datetime as _dt, timedelta, timezone
                    # Determine target weekday from original text
                    weekday_match = re.search(r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', text_lower_check)
                    weekday = weekday_match.group(1) if weekday_match else None
                    logger.info(f"Extracted weekday for quarterly: {weekday} from text: '{original_text}'")
                    
                    if weekday:
                        # Find the first Monday of the next quarter
                        # Quarters: Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec)
                        now = _dt.now()
                        current_quarter = (now.month - 1) // 3 + 1
                        next_quarter = current_quarter + 1
                        if next_quarter > 4:
                            next_quarter = 1
                            target_year = now.year + 1
                        else:
                            target_year = now.year
                        
                        # First month of next quarter
                        quarter_start_months = {1: 1, 2: 4, 3: 7, 4: 10}  # Jan, Apr, Jul, Oct
                        target_month = quarter_start_months[next_quarter]
                        
                        # Extract time component from start_time string
                        time_str = None
                        time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', str(event.start_time).lower())
                        if time_match:
                            hour = int(time_match.group(1))
                            minute = int(time_match.group(2)) if time_match.group(2) else 0
                            ampm = time_match.group(3).lower() if time_match.group(3) else None
                            # Convert to 12-hour format string
                            if ampm:
                                if ampm == 'pm' and hour != 12:
                                    hour += 12
                                elif ampm == 'am' and hour == 12:
                                    hour = 0
                            # Format as "10am" or "10:30am"
                            if minute > 0:
                                time_str = f"{hour % 12 or 12}:{minute:02d}{ampm or ('pm' if hour >= 12 else 'am')}"
                            else:
                                time_str = f"{hour % 12 or 12}{ampm or ('pm' if hour >= 12 else 'am')}"
                        
                        # If regex didn't find time, try parsing with dateparser as fallback
                        if not time_str:
                            start_dt = dateparser.parse(str(event.start_time))
                            if start_dt:
                                time_str = start_dt.strftime('%I:%M %p').lstrip('0').replace(':00 ', ' ').lower()
                        
                        # Determine ordinal (first, second, third, fourth, last)
                        ordinal_match = re.search(r'\b(first|second|third|fourth|last)\b', text_lower_check)
                        ordinal_str = ordinal_match.group(1).lower() if ordinal_match else "first"
                        ordinal_map = {"first": 0, "second": 1, "third": 2, "fourth": 3, "last": -1}
                        ordinal = ordinal_map.get(ordinal_str, 0)
                        
                        # Calculate the ordinal weekday in the target month
                        weekday_index = {
                            'monday':0,'tuesday':1,'wednesday':2,'thursday':3,
                            'friday':4,'saturday':5,'sunday':6
                        }[weekday]
                        
                        if ordinal == -1:  # Last
                            # Find last occurrence
                            if target_month == 12:
                                last_day = 31
                            elif target_month in [4, 6, 9, 11]:
                                last_day = 30
                            elif target_month == 2:
                                if (target_year % 4 == 0 and target_year % 100 != 0) or (target_year % 400 == 0):
                                    last_day = 29
                                else:
                                    last_day = 28
                            else:
                                last_day = 31
                            # Use UTC timezone for calculation, will be converted later
                            first_of_month = _dt(target_year, target_month, last_day, tzinfo=timezone.utc)
                            while first_of_month.weekday() != weekday_index:
                                first_of_month -= timedelta(days=1)
                            target_date = first_of_month
                        else:
                            # Find first occurrence, then add weeks
                            first_of_month = _dt(target_year, target_month, 1, tzinfo=timezone.utc)
                            days_until_first = (weekday_index - first_of_month.weekday()) % 7
                            first_occurrence = first_of_month + timedelta(days=days_until_first)
                            target_date = first_occurrence + timedelta(weeks=ordinal)
                        
                        # Apply time
                        if time_str:
                            time_match2 = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', time_str.lower())
                            if time_match2:
                                hour = int(time_match2.group(1))
                                minute = int(time_match2.group(2)) if time_match2.group(2) else 0
                                ampm = time_match2.group(3).lower() if time_match2.group(3) else None
                                if ampm:
                                    if ampm == 'pm' and hour != 12:
                                        hour += 12
                                    elif ampm == 'am' and hour == 12:
                                        hour = 0
                                target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # Format new start_time
                        month_names = ['January','February','March','April','May','June',
                                      'July','August','September','October','November','December']
                        month_name = month_names[target_month - 1]
                        new_start = f"{ordinal_str.capitalize()} {weekday.capitalize()} of {month_name} {target_year}"
                        if time_str:
                            new_start += f" at {time_str}"
                        logger.info(f"Adjusting start_time for quarterly pattern: '{event.start_time}' -> '{new_start}'")
                        if hasattr(event, 'model_copy'):
                            event = event.model_copy(update={"start_time": new_start})
                        else:
                            event = event.copy(update={"start_time": new_start})
                
                # Check for month range patterns
                # Check for "for the whole of [month]" or "for [month]" or "during [month]" patterns
                # Also check for "for next month" or "for this month" (finite duration)
                # Also check if end_date contains a month name (indicates month range)
                has_month_range_check = bool(re.search(r'\bfor\s+(the\s+whole\s+of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)', text_lower_check)) or \
                                         bool(re.search(r'\bduring\s+(january|february|march|april|may|june|july|august|september|october|november|december)', text_lower_check)) or \
                                         bool(re.search(r'\bfor\s+(next|this)\s+month\b', text_lower_check)) or \
                                         (isinstance(event.end_date, str) and bool(re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', event.end_date.lower())))
                
                if has_month_range_check and recurrence_enum != RecurrenceType.NONE:
                    logger.info(f"Month range pattern detected, adjusting start_time: '{original_text}'")
                    import dateparser
                    import calendar
                    from datetime import datetime as _dt
                    # Determine target weekday from original text
                    weekday_match = re.search(r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', text_lower_check)
                    weekday = weekday_match.group(1) if weekday_match else None
                    logger.info(f"Extracted weekday: {weekday} from text: '{original_text}'")

                    # Determine target month from end_date or text
                    month = None
                    if isinstance(event.end_date, str):
                        # end_date like 'last Tuesday of December' or 'December 31'
                        m = re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', event.end_date.lower())
                        if m:
                            month = m.group(1)
                            logger.info(f"Extracted month from end_date: {month}")
                    if not month:
                        # Check for "for next month" or "for this month"
                        next_month_match = re.search(r'\bfor\s+next\s+month\b', text_lower_check)
                        this_month_match = re.search(r'\bfor\s+this\s+month\b', text_lower_check)
                        if next_month_match or this_month_match:
                            # Calculate the target month
                            now = _dt.now()
                            if next_month_match:
                                if now.month == 12:
                                    target_month_num = 1
                                else:
                                    target_month_num = now.month + 1
                            else:  # this month
                                target_month_num = now.month
                            month_names = ['january','february','march','april','may','june',
                                          'july','august','september','october','november','december']
                            month = month_names[target_month_num - 1]
                            logger.info(f"Extracted month from 'for next/this month': {month}")
                        else:
                            # Try to find month name in text
                            m = re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', text_lower_check)
                            if m:
                                month = m.group(1)
                                logger.info(f"Extracted month from text: {month}")

                    if weekday and month:
                        # Extract time component from start_time string using regex (more reliable)
                        time_str = None
                        time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', str(event.start_time).lower())
                        if time_match:
                            hour = int(time_match.group(1))
                            minute = int(time_match.group(2)) if time_match.group(2) else 0
                            ampm = time_match.group(3).lower() if time_match.group(3) else None
                            # Convert to 12-hour format string
                            if ampm:
                                if ampm == 'pm' and hour != 12:
                                    hour += 12
                                elif ampm == 'am' and hour == 12:
                                    hour = 0
                            # Format as "7pm" or "7:30pm"
                            if minute > 0:
                                time_str = f"{hour % 12 or 12}:{minute:02d}{ampm or ('pm' if hour >= 12 else 'am')}"
                            else:
                                time_str = f"{hour % 12 or 12}{ampm or ('pm' if hour >= 12 else 'am')}"
                        
                        # If regex didn't find time, try parsing with dateparser as fallback
                        if not time_str:
                            start_dt = dateparser.parse(str(event.start_time))
                            if start_dt:
                                time_str = start_dt.strftime('%I:%M %p').lstrip('0').replace(':00 ', ' ').lower()
                        
                        # Compute first weekday of the month
                        now = _dt.now()
                        year = now.year
                        month_index = [
                            'january','february','march','april','may','june',
                            'july','august','september','october','november','december'
                        ].index(month) + 1
                        
                        # If target month has already passed this year, use next year
                        if month_index < now.month or (month_index == now.month and now.day > 15):
                            year += 1
                        
                        weekday_index = {
                            'monday':0,'tuesday':1,'wednesday':2,'thursday':3,
                            'friday':4,'saturday':5,'sunday':6
                        }[weekday]
                        cal = calendar.Calendar()
                        first_day = None
                        for d in cal.itermonthdates(year, month_index):
                            if d.month == month_index and d.weekday() == weekday_index:
                                first_day = d
                                break
                        if first_day:
                            month_name = month.capitalize()
                            new_start = f"{month_name} {first_day.day}"
                            if time_str:
                                new_start += f" at {time_str}"
                            logger.info(f"Adjusting start_time for month range: '{event.start_time}' -> '{new_start}'")
                            if hasattr(event, 'model_copy'):
                                event = event.model_copy(update={"start_time": new_start})
                            else:
                                event = event.copy(update={"start_time": new_start})
                        else:
                            logger.warning(f"Could not find first {weekday} in {month} {year}")
            except Exception as month_adj_err:
                logger.warning(f"Failed to adjust start_time for month range: {month_adj_err}")

            # Check if this looks like an indefinite recurring event (e.g., "Every Monday" without "for X weeks")
            # If so, strip any count that was incorrectly set OR ensure count is None for indefinite events
            # BUT preserve count for finite patterns like "this week", "next week", "this weekend", etc.
            try:
                if recurrence_enum != RecurrenceType.NONE and not event.end_date:
                    # Check if original text suggests indefinite recurring event
                    text_lower = original_text.lower()
                    # Patterns that suggest indefinite: "every [day]" without "for X" or "until"
                    has_indefinite_pattern = (
                        bool(re.search(r'\bevery\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|day|weekday|weekend|week|month|year)', text_lower)) or
                        bool(re.search(r'\beach\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|day|weekday|weekend|week|month|year)', text_lower))
                    )
                    # Check if there's NO explicit count or end date mentioned
                    # Look for "for X weeks/months/days", "for the next X months", "for next X months" patterns
                    # Must have "for" keyword (with optional "the next" or "next" in between)
                    has_explicit_count = bool(re.search(r'\bfor\s+(?:the\s+)?(?:next\s+)?(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+(weeks?|months?|days?|years?)', text_lower)) or \
                                        bool(re.search(r'\bnext\s+(\d+|two|three|four|five|six|seven|eight|nine|ten)\s+(weeks?|months?|days?|years?)', text_lower))
                    has_until = bool(re.search(r'\buntil\s+', text_lower))
                    # Check for "for the whole of [month]" or "for [month]" or "during [month]" patterns
                    # Also check for "for next month" or "for this month" (finite duration)
                    # Also check if end_date contains a month name (indicates month range)
                    has_month_range = bool(re.search(r'\bfor\s+(the\s+whole\s+of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)', text_lower)) or \
                                     bool(re.search(r'\bduring\s+(january|february|march|april|may|june|july|august|september|october|november|december)', text_lower)) or \
                                     bool(re.search(r'\bfor\s+(next|this)\s+month\b', text_lower)) or \
                                     (isinstance(event.end_date, str) and bool(re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', event.end_date.lower())))
                    
                    # Check for finite patterns that should preserve the count (e.g., "this week", "next week", "this weekend")
                    has_finite_pattern = bool(re.search(r'\b(this|next)\s+(week|weekend)', text_lower))
                    
                    # Log for debugging
                    logger.info(f"Checking indefinite recurring event: text='{original_text}', has_indefinite={has_indefinite_pattern}, has_explicit={has_explicit_count}, has_until={has_until}, has_finite={has_finite_pattern}, has_month_range={has_month_range}, count={recurrence_count}, end_date={event.end_date}")
                    
                    # If it has an explicit count/duration (like "for the next 3 months"), preserve the count - it's NOT indefinite
                    if has_explicit_count:
                        logger.info(f"Preserving recurrence_count for explicit duration: '{original_text}' (count={recurrence_count})")
                        # Don't modify recurrence_count - it should be expanded into multiple events
                    # If it's a finite pattern (like "this week"), preserve the count - don't make it indefinite
                    elif has_finite_pattern:
                        logger.info(f"Preserving recurrence_count for finite pattern: '{original_text}' (count={recurrence_count})")
                        # Don't modify recurrence_count for finite patterns
                    # If it has a month range pattern (like "for the whole of December"), it's NOT indefinite
                    elif has_month_range:
                        logger.info(f"Month range pattern detected, ensuring end_date is set: '{original_text}'")
                        # If LLM didn't set end_date, try to set it based on the pattern
                        if event.end_date is None:
                            # Check for "for next month" or "for this month" patterns
                            next_month_match = re.search(r'\bfor\s+next\s+month\b', text_lower)
                            this_month_match = re.search(r'\bfor\s+this\s+month\b', text_lower)
                            
                            if next_month_match or this_month_match:
                                # Determine target month
                                from datetime import datetime as _dt
                                now = _dt.now()
                                if next_month_match:
                                    if now.month == 12:
                                        target_month = 1
                                        target_year = now.year + 1
                                    else:
                                        target_month = now.month + 1
                                        target_year = now.year
                                else:  # this month
                                    target_month = now.month
                                    target_year = now.year
                                
                                # Find the weekday from the text
                                weekday_match = re.search(r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', text_lower)
                                if weekday_match:
                                    weekday = weekday_match.group(1)
                                    # Set end_date to last occurrence of that weekday in the target month
                                    month_names = ['january','february','march','april','may','june',
                                                  'july','august','september','october','november','december']
                                    month_name = month_names[target_month - 1]
                                    end_date_str = f"last {weekday} of {month_name}"
                                    logger.info(f"Setting end_date for 'for next/this month' pattern: '{end_date_str}'")
                                    if hasattr(event, 'model_copy'):
                                        event = event.model_copy(update={"end_date": end_date_str})
                                    else:
                                        event = event.copy(update={"end_date": end_date_str})
                            else:
                                logger.warning(f"Month range pattern detected but end_date is None - LLM should have set it: '{original_text}'")
                        # Note: start_time adjustment is now handled above, before this block
                    # If it looks like indefinite recurring event, ensure count is None
                    # This handles both cases: when LLM incorrectly sets a count, or when count is already None
                    elif has_indefinite_pattern and not has_explicit_count and not has_until and not has_month_range:
                        if recurrence_count is not None:
                            logger.info(f"Stripping recurrence_count for indefinite recurring event: '{original_text}' (was {recurrence_count})")
                        else:
                            logger.info(f"Confirming indefinite recurring event (count already None): '{original_text}'")
                        recurrence_count = None
                    # Also check: if no explicit count or until mentioned, and pattern suggests indefinite, make it indefinite
                    elif not has_explicit_count and not has_until and not has_month_range and recurrence_count is not None:
                        # If no explicit count/until but LLM set a count, check if it's a simple recurring pattern
                        if has_indefinite_pattern or bool(re.search(r'\bevery\b|\beach\b', text_lower)):
                            logger.info(f"Removing count for indefinite recurring event pattern: '{original_text}' (was {recurrence_count})")
                            recurrence_count = None
            except Exception as e:
                logger.error(f"Error checking indefinite recurring event: {e}", exc_info=True)

            # Use model_copy for Pydantic v2, or copy for v1
            if hasattr(event, 'model_copy'):
                return event.model_copy(update={
                    "recurrence_type": recurrence_enum,
                    "recurrence_count": recurrence_count,
                    "recurrence_interval": recurrence_interval
                })
            else:
                return event.copy(update={
                    "recurrence_type": recurrence_enum,
                    "recurrence_count": recurrence_count,
                    "recurrence_interval": recurrence_interval
                })

        except Exception as e:
            logger.warning(f"Failed to normalize recurrence information: {e}")
            return event
    
    def _validate_events(self, events: List[ParsedEvent]) -> bool:
        """Validate events before returning them."""
        if not events:
            return False
        
        for event in events:
            # Check required fields
            if not event.title or len(event.title.strip()) < 2:
                logger.error(f"Invalid title: {event.title}")
                return False
            
            if not event.start_time:
                logger.error("Missing start_time")
                return False
            
            # Check duration is reasonable (max 7 days for long conferences/events)
            # Skip duration validation if end_time is set (date range trips use end_time instead of duration)
            if not event.end_time:
                if event.duration_minutes < 5 or event.duration_minutes > 10080:  # 7 days = 10080 minutes
                    logger.error(f"Invalid duration: {event.duration_minutes}")
                    return False
            # If end_time is set, allow longer durations (for multi-day trips/vacations)
            
            # Validate recurrence_type
            valid_types = ["none", "daily", "weekly", "monthly", "yearly"]
            if event.recurrence_type not in valid_types:
                logger.error(f"Invalid recurrence_type: {event.recurrence_type}")
                return False
        
        return True
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text with version and model."""
        text_key = hashlib.md5(text.lower().strip().encode()).hexdigest()
        model = getattr(self, "model", "unknown")
        return f"{CACHE_VERSION}_{model}_{text_key}"
    
    def _get_system_prompt(self) -> str:
        return """You are an expert at parsing natural language event descriptions into structured calendar events.

CRITICAL RULES:
1. ALWAYS return valid JSON - no markdown, no code blocks
2. Dates MUST be in natural language format ("next Tuesday at 1pm")
3. Location MUST be extracted from "at [location]" or "in [location]"
4. For recurring events, ALWAYS set recurrence_type correctly
5. Time ranges MUST use "at [start] - [end]" format and ensure end >= start
6. If unclear, return empty events array

You understand:
- Single events: "Lunch with Sarah next Tuesday at 1pm"
- Recurring events: "Every Monday workshop at 9am for 3 hours for 4 weeks"
- Time ranges: "Meeting at 9am -11am" (same day, different times)
- Date range trips: "Vacation from Nov 22 - Dec 28" or "Ski trip Dec 20 to Jan 5" (single long event spanning the dates)
- Date range recurring: "Daily meetings from Monday - Friday" (daily recurring events across the range)
- Locations: "at Greenacre gym", "in conference room 3"
- Relative times: "tomorrow", "next week", "in 2 hours"
- Complex patterns: "Every other Tuesday", "First Monday of each month"
- End conditions: "for 3 months", "until December 15th"
- Buffer times: "30-minute meeting with 15-minute buffer before and after"

VALIDATION CHECKLIST:
□ title is present and meaningful
□ start_time is natural language (not empty)
□ duration_minutes is positive integer (5-10080, max 7 days for long conferences/events)
□ recurrence_type is one of: none, daily, weekly, monthly, yearly
□ If end_time is present, it must be after start_time; otherwise leave end_time null and rely on duration_minutes
□ JSON structure matches exactly"""
    
    def _build_prompt(self, text: str, timezone: str) -> str:
        return f"""Parse the following event description into structured event data.

Current timezone: {timezone}
Current date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Event description: "{text}"

Instructions:
1. Extract the event title, preserving the full title as written by the user
   - ALWAYS preserve the complete title phrase when the user writes it explicitly (e.g., "Doctor's appointment" → "Doctor's appointment", NOT "Doctor")
   - For descriptive phrases like "Doctor's appointment", "Job interview", "Team meeting", "Family dinner", preserve the full phrase
   - Only simplify generic single-word titles (e.g., "Meeting tomorrow at 2pm" → "Meeting")
   - CRITICAL: For recurring events, REMOVE recurrence words from the title (e.g., "Every", "Each", "First", "Last", weekday names when they're part of the recurrence pattern)
     * "Every Monday meeting at 2pm" → title: "Meeting" (NOT "Every Monday meeting")
     * "Every Tuesday workout at 6am" → title: "Workout" (NOT "Every Tuesday workout")
     * "Every Sunday morning run at 7am" → title: "Morning run" (NOT "Every Sunday morning run")
     * "First Monday of every month board meeting at 9am" → title: "Board meeting" (NOT "First Monday of every month board meeting")
     * "Last Friday of each month team review at 3pm" → title: "Team review" (NOT "Last Friday of each month team review")
     * "Every other Tuesday mentoring session at 5pm" → title: "Mentoring session" (NOT "Every other Tuesday mentoring session")
     * The recurrence information is stored in recurrence_type, recurrence_interval, etc. - don't include it in the title
   - ALWAYS provide a meaningful title (minimum 2 characters)
   - If no clear title is given, create one based on the activity described
   - Examples: "Doctor's appointment next Friday" → "Doctor's appointment", "Lunch with Sarah" → "Lunch with Sarah", "Meeting tomorrow at 2pm" → "Meeting"
 2. Parse the start time into natural language format (e.g., "next Tuesday at 1pm")
    - CRITICAL: ALWAYS include the time in start_time if it's mentioned in the input, even if it appears before the date word
      * "Meeting 7pm tomorrow" → start_time: "tomorrow at 7pm" (NOT "tomorrow" without time, and title should be "Meeting" not "Meeting 7pm")
      * "Lunch 12pm today" → start_time: "today at 12pm" (NOT "today" without time)
      * "Appointment 3pm next Friday" → start_time: "next Friday at 3pm" (NOT "next Friday" without time)
      * Extract the time from anywhere in the input and combine it with the date in start_time
    - CRITICAL: For standalone weekday names (without "next" or "this"), use "this [day]" meaning the upcoming occurrence
      * "on Thursday at 3pm" or "Thursday at 3pm" → start_time: "this Thursday at 3pm" (NOT "next Thursday at 3pm")
      * Only use "next [day]" when the user explicitly says "next"
      * Examples: "coffee on Thursday" → "this Thursday", "meeting Friday" → "this Friday"
    - CRITICAL: For recurring events like "Every day standup at 5pm" or "Every Monday meeting at 2pm", set start_time to a specific date/time, NOT the recurrence pattern
      * "Every day standup at 5pm" → start_time: "today at 5pm" (not "every day at 5pm")
      * "Every Monday meeting at 2pm" → start_time: "next Monday at 2pm" (not "every Monday at 2pm")
      * Extract ONLY the time/date from the description, not the recurrence words like "every", "each", etc.
3. If a time range is specified (e.g., "9am -11am"), set end_time accordingly
4. Extract location if mentioned (patterns: "at [location]", "in [location]")
5. For duration: "for X hours/days/minutes" is a DURATION for a SINGLE event, NOT recurrence
   - Example: "Conference on January 5th at 9am for 2 days" = single 48-hour event
   - Convert to duration_minutes: "2 days" = 2880 minutes, "6 hours" = 360 minutes
6. For recurring events, determine:
   - recurrence_type: "daily", "weekly", "monthly", "yearly", or "none"
   - recurrence_count: number of occurrences - CRITICAL: ONLY set a number if explicitly specified (e.g., "for 4 weeks", "for 3 months"). If user says "Every Monday" or "Every day" without "for X weeks/months" or "until [date]", set recurrence_count to null (unlimited/indefinite)
   - recurrence_interval: for "every other" patterns, set to 2
   - end_date or end_after_count: if "for X months/weeks" or "until [date]" is specified
   - CRITICAL: "Monday for the next 6 months" / "for the next 6 months meeting every Monday" is ONE weekly recurring series. Set recurrence_type "weekly", start_time to the next that weekday, and end_date about 6 months later. Do NOT emit many separate events and do NOT leave recurrence_type as "none".
   - CRITICAL: "for the whole of [month]" or "for [month]" or "during [month]" → set end_date to "last [day] of [month]" (e.g., "for the whole of December" → end_date: "last Tuesday of December" or "December 31")
   - "from DATE - DATE" or "DATE - DATE" patterns: 
     - CRITICAL: If title contains "trip", "vacation", "holiday", or "conference" → ALWAYS single event (recurrence_type: "none")
       * Set start_time to first DATE (with default time like "9am" if no time specified)
       * Set end_time to second DATE (with default time like "5pm" if no time specified)
       * Set recurrence_type to "none" (NOT "daily")
       * Set duration_minutes to default (60) - DO NOT calculate from date range
       * Example: "Holiday trip from 22nd November - 28th December" → start_time: "22nd November at 9am", end_time: "28th December at 5pm", recurrence_type: "none", duration_minutes: 60
     - For recurring activities (without trip/vacation keywords): recurrence_type "daily", start_time to first DATE, end_date to second DATE
       * Example: "Daily meetings from Monday - Friday" → recurrence_type: "daily", start_time: "next Monday", end_date: "next Friday"
    - "first Monday of each month" or "last Friday of each month": recurrence_type "monthly", start_time = next matching date at the specified time, recurrence_interval = 1
    - "first Monday of every quarter" or "last Friday of each quarter": recurrence_type "monthly", start_time = first matching date in next quarter (January, April, July, or October) at the specified time, recurrence_interval = 3 (every 3 months)
    - "for the whole week" or "for the entire week" or "all week" or "for the whole of next week": recurrence_type "daily", recurrence_count = 7 (full week Mon-Sun)
    - "for next week" (without "whole" or "every day"): recurrence_type "daily", start_time = first day of next week, recurrence_count = 5 (weekdays only)
    - "this week" or "every day this week" or "every day next week": recurrence_type "daily", recurrence_count = 7 (full week Mon-Sun)
    - "this weekend" or "next weekend": recurrence_type "daily", recurrence_count = 2, start_time = "this Saturday" or "next Saturday", covers Saturday and Sunday only
    - If user explicitly says "weekdays" or "business days": recurrence_count = 5 (Mon-Fri only)
   - For "Create X meetings/events/appointments every day this week": ignore the number X, use "this week" pattern (7 events for full week)
7. Extract buffer times if mentioned:
   - "with X minute buffer before" → buffer_before: X
   - "with X minute buffer after" → buffer_after: X
   - "with X minute buffer before and after" → buffer_before: X, buffer_after: X
   - Do NOT put buffer info in notes; use buffer_before and buffer_after fields
8. If multiple distinct events are described (separated by "and", "also", etc.), create multiple event objects
9. If no explicit date or time is given, set start_time to "now" and leave end_time null; rely on duration_minutes

Return JSON with this structure:
{{
  "events": [
    {{
      "title": "string",
      "start_time": "natural language time",
      "end_time": "natural language time or null",
      "duration_minutes": 60,
      "location": "location or null",
      "notes": "additional notes or null",
      "color": "hex color or null",
      "reminder": "reminder setting or null",
      "recurrence_type": "none|daily|weekly|monthly|yearly",
      "recurrence_count": null,
      "recurrence_interval": 1,
      "recurrence_days": null,
      "buffer_before": 0,
      "buffer_after": 0,
      "end_date": null,
      "end_after_count": null,
      "skip_dates": null
    }}
  ]
}}"""

