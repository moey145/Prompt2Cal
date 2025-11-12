"""
Date and time parsing utilities for event parsing.
Handles manual date parsing, timezone conversion, and natural language date processing.
"""

import re
import logging
import calendar
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pytz
import dateparser

logger = logging.getLogger(__name__)

class DateParser:
    """Handles parsing of dates and times from natural language."""
    
    def __init__(self):
        pass
    
    def parse_start_time(self, time_string: str, local_tz: pytz.timezone) -> Optional[datetime]:
        """
        Parse a start time string into a datetime object.
        Tries manual parsing first, then falls back to dateparser.
        """
        if not time_string:
            return None
        
        # Check if it's already an ISO datetime string
        if time_string.startswith('20') and ('T' in time_string or ' ' in time_string):
            try:
                # Try to parse as ISO datetime
                dt = datetime.fromisoformat(time_string.replace('Z', '+00:00'))
                # Convert to local timezone if needed
                if dt.tzinfo is None:
                    dt = local_tz.localize(dt)
                elif dt.tzinfo != local_tz:
                    dt = dt.astimezone(local_tz)
                logger.info(f"Parsed ISO datetime: '{time_string}' -> {dt}")
                return dt
            except ValueError:
                pass  # Not a valid ISO datetime, continue with normal parsing
            
        logger.info(f"Trying manual date parsing first for: '{time_string}'")
        
        # Try manual parsing first
        manual_result = self._manual_date_parse(time_string, local_tz)
        if manual_result:
            logger.info(f"Manual parsing succeeded: '{time_string}' -> {manual_result}")
            return manual_result
        
        # Fall back to dateparser
        logger.info(f"Manual parsing failed, trying dateparser...")
        try:
            logger.info(f"Parsing start time: '{time_string}' with current time: {datetime.now(local_tz)}")
            
            # Try with timezone settings first
            parsed = dateparser.parse(time_string, settings={
                'TIMEZONE': str(local_tz),
                'RETURN_AS_TIMEZONE_AWARE': True,
                'PREFER_DATES_FROM': 'future'
            })
            
            if parsed:
                logger.info(f"Dateparser succeeded with settings: {parsed}")
                return parsed
            
            # Try without settings
            logger.info("Failed to parse with settings, trying without settings...")
            parsed = dateparser.parse(time_string)
            
            if parsed:
                logger.info(f"Dateparser succeeded without settings: {parsed}")
                # Localize if not timezone aware
                if parsed.tzinfo is None:
                    parsed = local_tz.localize(parsed)
                return parsed
                
        except Exception as e:
            logger.warning(f"Dateparser failed: {e}")
        
        # Final fallback to current time
        logger.warning(f"Could not parse start time '{time_string}', using fallback")
        return datetime.now(local_tz)
    
    def _manual_date_parse(self, date_string: str, local_tz: pytz.timezone) -> Optional[datetime]:
        """
        Manual parsing for common date patterns.
        Returns None if pattern doesn't match.
        """
        try:
            now = datetime.now(local_tz)
            original_string = date_string
            date_string_lower = date_string.lower().strip()
            
            # Handle "first/second/third/fourth/last [weekday] of [month] [year]" patterns FIRST (e.g., "first Monday of January 2026 at 10am")
            # This is more specific than the "every month" pattern, so check it first
            ordinal_month_year_match = re.search(r'(first|second|third|fourth|1st|2nd|3rd|4th|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+of\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?', date_string_lower, re.IGNORECASE)
            if ordinal_month_year_match:
                ordinal_str = ordinal_month_year_match.group(1).lower()
                weekday_str = ordinal_month_year_match.group(2).lower()
                month_name = ordinal_month_year_match.group(3).lower()
                year = int(ordinal_month_year_match.group(4))
                
                # Normalize ordinal
                ordinal_map = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2, "fourth": 3, "4th": 3, "last": -1}
                ordinal = ordinal_map.get(ordinal_str, 0)
                
                # Map weekday names to numbers
                weekday_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                target_weekday = weekday_map[weekday_str]
                
                # Map month names to numbers
                month_map = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
                    'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
                    'may': 5, 'june': 6, 'jun': 6,
                    'july': 7, 'jul': 7, 'august': 8, 'aug': 8,
                    'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
                    'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                }
                month = month_map[month_name]
                
                # Parse time if present
                hour = 9  # Default to 9am
                minute = 0
                if ordinal_month_year_match.group(5):
                    hour = int(ordinal_month_year_match.group(5))
                    minute = int(ordinal_month_year_match.group(6)) if ordinal_month_year_match.group(6) else 0
                    ampm = ordinal_month_year_match.group(7).lower() if ordinal_month_year_match.group(7) else None
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                
                # Calculate the ordinal weekday in the month
                if ordinal == -1:  # Last
                    # Find last occurrence
                    if month == 12:
                        last_day = 31
                    elif month in [4, 6, 9, 11]:
                        last_day = 30
                    elif month == 2:
                        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                            last_day = 29
                        else:
                            last_day = 28
                    else:
                        last_day = 31
                    target_date = local_tz.localize(datetime(year, month, last_day, hour, minute))
                    while target_date.weekday() != target_weekday:
                        target_date -= timedelta(days=1)
                else:
                    # Find first occurrence, then add weeks
                    first_of_month = local_tz.localize(datetime(year, month, 1))
                    # Calculate days until first occurrence of target weekday
                    first_weekday = first_of_month.weekday()
                    days_until_first = (target_weekday - first_weekday) % 7
                    if days_until_first == 0 and first_weekday != target_weekday:
                        days_until_first = 7
                    first_occurrence = first_of_month + timedelta(days=days_until_first)
                    # Add weeks for ordinal (first=0, second=1, third=2, fourth=3)
                    target_date = first_occurrence + timedelta(weeks=ordinal)
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            # Handle "first/second/third/fourth/last [weekday] of every/each/next/this month at [time]" patterns
            ordinal_pattern = re.compile(
                r'(first|second|third|fourth|1st|2nd|3rd|4th|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
                r'\s+of\s+(?:every|the|each|next|this)\s+month(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?',
                re.IGNORECASE
            )
            ordinal_match = ordinal_pattern.search(date_string)
            if ordinal_match:
                ordinal_str = ordinal_match.group(1).lower()
                weekday_str = ordinal_match.group(2).lower()
                month_type_match = re.search(r'\s+of\s+(every|the|each|next|this)\s+month', date_string)
                month_type = month_type_match.group(1).lower() if month_type_match else None
                
                # Normalize ordinal
                ordinal_map = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2, "fourth": 3, "4th": 3, "last": -1}
                ordinal = ordinal_map.get(ordinal_str, 0)
                
                # Parse time
                if ordinal_match.group(3):
                    hour = int(ordinal_match.group(3))
                    minute = int(ordinal_match.group(4)) if ordinal_match.group(4) else 0
                    ampm = ordinal_match.group(5).lower() if ordinal_match.group(5) else None
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                else:
                    hour = 9  # Default to 9am if no time specified
                    minute = 0
                
                # For "this month", calculate for current month; for "next month", calculate for next month
                # For "last" ordinal with "this month", we need to check if it's already passed
                if month_type == 'this' and ordinal == -1:  # "last [weekday] of this month"
                    # Use the current month
                    target_month = now.month
                    target_year = now.year
                    weekday_map = {
                        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                        "friday": 4, "saturday": 5, "sunday": 6
                    }
                    target_weekday = weekday_map.get(weekday_str.lower())
                    if target_weekday is not None:
                        # Find last occurrence in current month
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
                        target_date = local_tz.localize(datetime(target_year, target_month, last_day))
                        while target_date.weekday() != target_weekday:
                            target_date -= timedelta(days=1)
                        target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        # If the date has already passed, use next month
                        if target_date < now:
                            if target_month == 12:
                                target_month = 1
                                target_year += 1
                            else:
                                target_month += 1
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
                            target_date = local_tz.localize(datetime(target_year, target_month, last_day))
                            while target_date.weekday() != target_weekday:
                                target_date -= timedelta(days=1)
                            target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        logger.info(f"Manual parsing ordinal weekday (this month): '{original_string}' -> {target_date}")
                        return target_date
                
                # Calculate next occurrence (for other cases)
                result = self._next_ordinal_weekday_in_month(now, ordinal, weekday_str, hour, minute, local_tz)
                if result:
                    logger.info(f"Manual parsing ordinal weekday: '{original_string}' -> {result}")
                    return result
            
            # Handle time-only strings like "at 5pm" or "5pm" (for recurring events like "Every day standup at 5pm")
            # Extract just the time part and use today's date
            # ONLY match if there's NO specific date/day reference (like "next Friday", "tomorrow", "today", weekday names, etc.)
            # Allow "every" and "each" as they indicate recurrence patterns, not specific dates
            # Check for specific date keywords first
            has_specific_date_keyword = bool(re.search(
                r'\b(next|this|last|tomorrow|today|tonight|yesterday)\b',
                date_string,
                re.IGNORECASE
            ))
            # Check for weekday names that are NOT preceded by "every" or "each" (e.g., "Friday" but not "every Friday")
            has_standalone_weekday = bool(re.search(
                r'(?<!\bevery\s)(?<!\beach\s)\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                date_string,
                re.IGNORECASE
            ))
            # Check for month names (e.g., "December", "Dec", "January", "Jan", etc.)
            has_month_name = bool(re.search(
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
                date_string,
                re.IGNORECASE
            ))
            has_specific_date = has_specific_date_keyword or has_standalone_weekday or has_month_name
            
            if not has_specific_date:
                # Match "at 5pm" anywhere in the string (for cases like "every day at 5pm"), or just "5pm" at the start/end
                time_only_pattern = re.compile(r'\bat\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)\b|^(\d{1,2})(?::(\d{2}))?\s*([ap]m)$', re.IGNORECASE)
                time_only_match = time_only_pattern.search(date_string)
                if time_only_match:
                    # Handle two pattern alternatives: "at 5pm" (groups 1,2,3) or "5pm" (groups 4,5,6)
                    if time_only_match.group(1):  # "at 5pm" pattern matched
                        hour = int(time_only_match.group(1))
                        minute = int(time_only_match.group(2)) if time_only_match.group(2) else 0
                        ampm = time_only_match.group(3).lower() if time_only_match.group(3) else None
                    else:  # "5pm" pattern matched
                        hour = int(time_only_match.group(4))
                        minute = int(time_only_match.group(5)) if time_only_match.group(5) else 0
                        ampm = time_only_match.group(6).lower() if time_only_match.group(6) else None
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    
                    # Use today's date with the specified time
                    target_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # If the time has already passed today, use tomorrow
                    if target_date <= now:
                        target_date = target_date + timedelta(days=1)
                    
                    logger.info(f"Manual parsing time-only: '{original_string}' -> {target_date}")
                    return target_date
              
              # Handle "today" patterns
            if 'today' in date_string:
                target_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Extract time if present - improved regex to handle both "at 7pm" and "7pm" patterns
                # Try "at 7pm" pattern first, then try "7pm" pattern (without "at")
                time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', date_string, re.IGNORECASE)
                if not time_match:
                    # Try pattern without "at" (e.g., "today 7pm" or "7pm today")
                    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap]m)', date_string, re.IGNORECASE)
                
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3).lower() if time_match.group(3) else None
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parsing 'today': {original_string} -> {target_date}")
                return target_date
            
            # Handle "day after tomorrow" patterns
            if 'day after tomorrow' in date_string:
                target_date = now + timedelta(days=2)
                
                # Extract time if present - improved regex to handle both "at 7pm" and "7pm" patterns
                time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', date_string, re.IGNORECASE)
                if not time_match:
                    # Try pattern without "at" (e.g., "day after tomorrow 7pm" or "7pm day after tomorrow")
                    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap]m)', date_string, re.IGNORECASE)
                
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3).lower() if time_match.group(3) else None
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parsing 'day after tomorrow': {original_string} -> {target_date}")
                return target_date
            
            # Handle "tomorrow" patterns
            if 'tomorrow' in date_string:
                target_date = now + timedelta(days=1)
                
                # Extract time if present - improved regex to handle both "at 7pm" and "7pm" patterns
                time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', date_string, re.IGNORECASE)
                if not time_match:
                    # Try pattern without "at" (e.g., "tomorrow 7pm" or "7pm tomorrow")
                    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*([ap]m)', date_string, re.IGNORECASE)
                
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3).lower() if time_match.group(3) else None
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parsing 'tomorrow': {original_string} -> {target_date}")
                return target_date
            
            # Handle "tonight at <time>" patterns
            if 'tonight' in date_string:
                target_date = now.replace(hour=0, minute=0, second=0, microsecond=0)  # Start of today
                
                # Extract time if present
                time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', date_string)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume PM for "tonight"
                        hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 7pm if no time specified
                    target_date = target_date.replace(hour=19, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parsing 'tonight': {original_string} -> {target_date}")
                return target_date
            
            # Handle "every weekday at <time>" patterns
            if 'every weekday' in date_string:
                # Find next weekday (Monday-Friday)
                target_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                days_ahead = 0
                while target_date.weekday() >= 5:  # Saturday=5, Sunday=6
                    days_ahead += 1
                    target_date = now + timedelta(days=days_ahead)
                    target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Extract time if present
                time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', date_string)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume AM for weekday meetings
                        pass  # Keep as-is for AM times
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 9am if no time specified
                    target_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parsing 'every weekday': {original_string} -> {target_date}")
                return target_date
            
            # Handle "every [weekday] in [month]" patterns (e.g., "every Wednesday in November at 6:30pm")
            every_weekday_month_match = re.search(r'every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:in|this)\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', date_string_lower)
            if every_weekday_month_match:
                weekday_name = every_weekday_month_match.group(1)
                month_name = every_weekday_month_match.group(2)
                
                # Map weekday names to numbers (Monday=0, Sunday=6)
                weekday_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                target_weekday = weekday_map[weekday_name]
                
                # Map month names to numbers
                month_map = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2,
                    'march': 3, 'mar': 3, 'april': 4, 'apr': 4,
                    'may': 5, 'june': 6, 'jun': 6,
                    'july': 7, 'jul': 7, 'august': 8, 'aug': 8,
                    'september': 9, 'sep': 9, 'october': 10, 'oct': 10,
                    'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                }
                target_month = month_map[month_name]
                
                # Find the first occurrence of the target weekday in the target month
                current_year = now.year
                # If the target month is before the current month, use next year
                if target_month < now.month:
                    current_year += 1
                
                # Start from the first day of the target month
                first_of_month = local_tz.localize(datetime(current_year, target_month, 1))
                
                # Find the first occurrence of the target weekday
                days_until_target = (target_weekday - first_of_month.weekday()) % 7
                target_date = first_of_month + timedelta(days=days_until_target)
                
                # Extract time if present
                time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', date_string)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                logger.info(f"Manual parsing 'every {weekday_name} in {month_name}': {original_string} -> {target_date}")
                return target_date
            
            # Handle "X weeks from now at <time>" (e.g., "3 weeks from now at 2:30 PM")
            weeks_from_now_match = re.search(r'(?:(\d+)\s+weeks?\s+from\s+now)(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?', date_string)
            if weeks_from_now_match:
                weeks_ahead = int(weeks_from_now_match.group(1))
                target_date = now + timedelta(weeks=weeks_ahead)
                
                # Extract time if present
                if weeks_from_now_match.group(2):
                    hour = int(weeks_from_now_match.group(2))
                    minute = int(weeks_from_now_match.group(3)) if weeks_from_now_match.group(3) else 0
                    ampm = weeks_from_now_match.group(4)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            # Handle "[weekday] next week at <time>" patterns (e.g., "Monday next week at 3pm")
            weekday_next_week_match = re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+next\s+week(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?', date_string_lower)
            if weekday_next_week_match:
                weekday_name = weekday_next_week_match.group(1)
                weekday_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                target_weekday = weekday_map[weekday_name]
                
                # Get the start of next week (next Monday)
                days_until_next_monday = (7 - now.weekday()) % 7
                if days_until_next_monday == 0:
                    days_until_next_monday = 7  # If today is Monday, next Monday is in 7 days
                next_monday = now + timedelta(days=days_until_next_monday)
                
                # From next Monday, find the target weekday
                days_from_monday = target_weekday
                target_date = next_monday + timedelta(days=days_from_monday)
                target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Extract time if present
                if weekday_next_week_match.group(2):
                    hour = int(weekday_next_week_match.group(2))
                    minute = int(weekday_next_week_match.group(3)) if weekday_next_week_match.group(3) else 0
                    ampm = weekday_next_week_match.group(4)
                    
                    if ampm:
                        if ampm.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif ampm.lower() == 'am' and hour == 12:
                            hour = 0
                    
                    target_date = target_date.replace(hour=hour, minute=minute)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            # Handle "next week at <time>" patterns
            next_week_match = re.search(r'next\s+week(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?', date_string)
            if next_week_match:
                target_date = now + timedelta(weeks=1)
                
                # Extract time if present
                if next_week_match.group(1):
                    hour = int(next_week_match.group(1))
                    minute = int(next_week_match.group(2)) if next_week_match.group(2) else 0
                    ampm = next_week_match.group(3)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            # Handle "in X weeks at <time>" patterns (e.g., "in 3 weeks at 2:30pm")
            in_weeks_match = re.search(r'in\s+(\d+)\s+weeks?(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?', date_string)
            if in_weeks_match:
                weeks_ahead = int(in_weeks_match.group(1))
                target_date = now + timedelta(weeks=weeks_ahead)
                
                # Extract time if present
                if in_weeks_match.group(2):
                    hour = int(in_weeks_match.group(2))
                    minute = int(in_weeks_match.group(3)) if in_weeks_match.group(3) else 0
                    ampm = in_weeks_match.group(4)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            # Handle "next [day]" and "this [day]" patterns (e.g., "next Monday", "this Friday")
            next_day_match = re.search(r'(next|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?', date_string_lower)
            if next_day_match:
                keyword = next_day_match.group(1).lower()  # "next" or "this"
                day_name = next_day_match.group(2)
                days_of_week = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                target_day = days_of_week[day_name]
                
                current_weekday = now.weekday()
                
                if keyword == 'next':
                    # For "next [day]", always mean the day in the week AFTER the current week
                    # This means: find "this [day]" first, then add 7 days
                    days_to_this_day = (target_day - current_weekday) % 7
                    if days_to_this_day == 0:
                        # If today is the target day, "this [day]" is today (0 days)
                        # "next [day]" would be in 7 days (next week)
                        days_ahead = 7
                    else:
                        # "this [day]" is days_to_this_day away
                        # "next [day]" is that plus 7 more days (week after)
                        days_ahead = days_to_this_day + 7
                else:
                    # For "this [day]", find the next occurrence of that weekday
                    # This is the upcoming occurrence (could be today, tomorrow, or later this week)
                    days_ahead = (target_day - current_weekday) % 7
                    if days_ahead == 0:
                        # If today is the target day, "this [day]" means today
                        days_ahead = 0
                
                target_date = now + timedelta(days=days_ahead)
                target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Extract time if present
                if next_day_match.group(3):
                    hour = int(next_day_match.group(3))
                    minute = int(next_day_match.group(4)) if next_day_match.group(4) else 0
                    ampm = next_day_match.group(5)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            # Handle standalone weekday names (e.g., "Thursday at 3pm", "on Friday at 2pm")
            # These should mean "this [day]" (the upcoming occurrence), not "next [day]"
            standalone_weekday_match = re.search(r'(?:^|\s|on\s+)(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?(?:\s|$)', date_string_lower)
            # Only match if we haven't already matched "next" or "this" patterns above
            if standalone_weekday_match and not re.search(r'\b(next|this)\s+', date_string_lower):
                day_name = standalone_weekday_match.group(1)
                days_of_week = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                target_day = days_of_week[day_name]
                current_weekday = now.weekday()
                
                # For standalone weekday, treat as "this [day]" (upcoming occurrence)
                days_ahead = (target_day - current_weekday) % 7
                if days_ahead == 0:
                    # If today is the target day, use today
                    days_ahead = 0
                
                target_date = now + timedelta(days=days_ahead)
                target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Extract time if present
                if standalone_weekday_match.group(2):
                    hour = int(standalone_weekday_match.group(2))
                    minute = int(standalone_weekday_match.group(3)) if standalone_weekday_match.group(3) else 0
                    ampm = standalone_weekday_match.group(4)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parse result for standalone weekday '{original_string}': {target_date}")
                return target_date
            
            # Handle "Month Day at time" patterns (e.g., "Nov 12 at 1:15pm", "December 25 at 2:30pm", "March 10th at 6pm")
            month_day_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?', date_string_lower)
            if month_day_match:
                month_name = month_day_match.group(1)
                day = int(month_day_match.group(2))
                
                # Convert month name to number
                month_map = {
                    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
                    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
                    'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
                    'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
                }
                month = month_map.get(month_name.lower(), 1)
                
                # Get current year
                current_year = now.year
                
                # Create target date
                target_date = local_tz.localize(datetime(current_year, month, day))
                
                # If the date has already passed this year, use next year
                if target_date < now:
                    target_date = local_tz.localize(datetime(current_year + 1, month, day))
                
                # Extract time if present
                if month_day_match.group(3):
                    hour = int(month_day_match.group(3))
                    minute = int(month_day_match.group(4)) if month_day_match.group(4) else 0
                    ampm = month_day_match.group(5)
                    
                    logger.info(f"Extracted time: hour={hour}, minute={minute}, ampm={ampm}")
                    
                    # Convert to 24-hour format
                    if ampm:
                        if ampm == 'pm' and hour != 12:
                            hour += 12
                        elif ampm == 'am' and hour == 12:
                            hour = 0
                    elif hour < 12 and hour >= 1:
                        # If no am/pm specified and hour is 1-11, assume business hours
                        if hour <= 7:
                            hour += 12
                    
                    target_date = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            # Handle "last [weekday] of this month" or "last [weekday] of next month" patterns
            last_weekday_this_month_match = re.search(r'last\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+of\s+(this|next)\s+month', date_string_lower)
            if last_weekday_this_month_match:
                weekday_name = last_weekday_this_month_match.group(1)
                month_type = last_weekday_this_month_match.group(2)  # "this" or "next"
                
                # Map weekday names to weekday numbers (0=Monday, 6=Sunday)
                weekday_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                target_weekday = weekday_map[weekday_name]
                
                # Determine target month
                if month_type == 'this':
                    target_month = now.month
                    target_year = now.year
                else:  # next
                    if now.month == 12:
                        target_month = 1
                        target_year = now.year + 1
                    else:
                        target_month = now.month + 1
                        target_year = now.year
                
                # Find the last occurrence of the target weekday in the target month
                # Start from the last day of the month and go backwards
                if target_month == 12:
                    last_day_of_month = 31
                elif target_month in [4, 6, 9, 11]:
                    last_day_of_month = 30
                elif target_month == 2:
                    # Check for leap year
                    if (target_year % 4 == 0 and target_year % 100 != 0) or (target_year % 400 == 0):
                        last_day_of_month = 29
                    else:
                        last_day_of_month = 28
                else:
                    last_day_of_month = 31
                
                # Start from the last day and find the last occurrence of the target weekday
                target_date = local_tz.localize(datetime(target_year, target_month, last_day_of_month))
                while target_date.weekday() != target_weekday:
                    target_date -= timedelta(days=1)
                
                # Extract time if present in the original string
                time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', original_string)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3)
                    
                    if ampm:
                        if ampm.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif ampm.lower() == 'am' and hour == 12:
                            hour = 0
                    
                    target_date = target_date.replace(hour=hour, minute=minute)
                else:
                    # Default to 2pm if no time specified
                    target_date = target_date.replace(hour=14, minute=0)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            # Handle "last [weekday] in [month]" patterns (e.g., "last Monday in December")
            last_weekday_month_match = re.search(r'last\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(?:in|of)\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', date_string_lower)
            if last_weekday_month_match:
                weekday_name = last_weekday_month_match.group(1)
                month_name = last_weekday_month_match.group(2)
                
                # Map weekday names to weekday numbers (0=Monday, 6=Sunday)
                weekday_map = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                    'friday': 4, 'saturday': 5, 'sunday': 6
                }
                target_weekday = weekday_map[weekday_name]
                
                # Map month names to month numbers
                month_map = {
                    'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
                    'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
                    'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
                    'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
                }
                month = month_map[month_name]
                
                # Determine the year (current year or next year)
                current_year = now.year
                # If the month has already passed, use next year
                if month < now.month or (month == now.month and now.day > 15):
                    current_year += 1
                
                # Find the last occurrence of the target weekday in the month
                # Start from the last day of the month and go backwards
                if month == 12:
                    last_day_of_month = 31
                elif month in [4, 6, 9, 11]:
                    last_day_of_month = 30
                elif month == 2:
                    # Check for leap year
                    if (current_year % 4 == 0 and current_year % 100 != 0) or (current_year % 400 == 0):
                        last_day_of_month = 29
                    else:
                        last_day_of_month = 28
                else:
                    last_day_of_month = 31
                
                # Start from the last day and find the last occurrence of the target weekday
                target_date = local_tz.localize(datetime(current_year, month, last_day_of_month))
                while target_date.weekday() != target_weekday:
                    target_date -= timedelta(days=1)
                
                # Extract time if present in the original string
                time_match = re.search(r'at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?', original_string)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3)
                    
                    if ampm:
                        if ampm.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif ampm.lower() == 'am' and hour == 12:
                            hour = 0
                    
                    target_date = target_date.replace(hour=hour, minute=minute)
                else:
                    # Default to end of day
                    target_date = target_date.replace(hour=23, minute=59)
                
                logger.info(f"Manual parse result for '{original_string}': {target_date}")
                return target_date
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in manual date parsing: {e}")
            return None
    
    def _next_ordinal_weekday_in_month(self, now: datetime, ordinal: int, weekday_str: str, hour: int, minute: int, local_tz: pytz.timezone) -> Optional[datetime]:
        """
        Calculate the next occurrence of an ordinal weekday (e.g., first Monday) in the current or next month.
        
        Args:
            now: Current datetime
            ordinal: 0 for first, 1 for second, 2 for third, 3 for fourth, -1 for last
            weekday_str: Name of the weekday (monday, tuesday, etc.)
            hour: Hour (0-23)
            minute: Minute (0-59)
            local_tz: Timezone
            
        Returns:
            Datetime of the next occurrence, or None if invalid
        """
        weekday_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        target_weekday = weekday_map.get(weekday_str.lower())
        if target_weekday is None:
            return None
        
        # Try current month first
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        candidate = self._nth_weekday_in_month(start_of_month, ordinal, target_weekday, hour, minute, local_tz)
        
        if candidate and candidate > now:
            return candidate
        
        # If current month's occurrence has passed, try next month
        if start_of_month.month == 12:
            next_month = 1
            next_year = start_of_month.year + 1
        else:
            next_month = start_of_month.month + 1
            next_year = start_of_month.year
        
        start_of_next_month = start_of_month.replace(year=next_year, month=next_month)
        return self._nth_weekday_in_month(start_of_next_month, ordinal, target_weekday, hour, minute, local_tz)
    
    def _nth_weekday_in_month(self, base: datetime, ordinal: int, target_weekday: int, hour: int, minute: int, local_tz: pytz.timezone) -> Optional[datetime]:
        """
        Calculate the nth weekday in a given month.
        
        Args:
            base: Datetime representing the start of the month
            ordinal: 0 for first, 1 for second, 2 for third, 3 for fourth, -1 for last
            target_weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
            hour: Hour (0-23)
            minute: Minute (0-59)
            local_tz: Timezone
            
        Returns:
            Datetime of the nth weekday, or None if invalid
        """
        first_weekday, days_in_month = calendar.monthrange(base.year, base.month)
        
        if ordinal == -1:  # Last
            last_day = local_tz.localize(datetime(base.year, base.month, days_in_month, hour, minute))
            delta = (last_day.weekday() - target_weekday) % 7
            return last_day - timedelta(days=delta)
        
        # For first, second, third, fourth
        first_occurrence_day = 1 + (target_weekday - first_weekday) % 7
        day = first_occurrence_day + ordinal * 7
        
        if day > days_in_month:
            day -= 7
        
        naive = datetime(base.year, base.month, day, hour, minute)
        return local_tz.localize(naive)
      
    def parse_end_date(self, end_date_str: str, local_tz: pytz.timezone) -> Optional[datetime]:
        """
        Parse an end date string into a datetime object.
        Handles both natural language and ISO format dates.
        """
        try:
            logger.info(f"Processing end_date: '{end_date_str}' (type: {type(end_date_str)})")
            
            # Parse natural language end date (e.g., "December 20", "Dec 20", "Dec 20 2024", "this Sunday")
            if isinstance(end_date_str, str) and not end_date_str.startswith('20'):
                # Try manual parsing first for common patterns
                manual_result = self._manual_date_parse(end_date_str, local_tz)
                if manual_result:
                    logger.info(f"Manual parsing succeeded for end_date: '{end_date_str}' -> {manual_result}")
                    return manual_result
                
                # Try to parse natural language date with dateparser
                parsed_end = dateparser.parse(
                    end_date_str, 
                    settings={
                        'TIMEZONE': str(local_tz),
                        'PREFER_DATES_FROM': 'future',
                        'RELATIVE_BASE': datetime.now(local_tz).replace(tzinfo=None)
                    }
                )
                logger.info(f"Dateparser result for '{end_date_str}': {parsed_end}")
                if parsed_end:
                    end_datetime = parsed_end
                    if end_datetime.tzinfo is None:
                        end_datetime = local_tz.localize(end_datetime)
                    return end_datetime
                else:
                    logger.warning(f"Could not parse end_date: {end_date_str}")
                    return None
            else:
                # Assume it's already in ISO format
                end_datetime = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                if end_datetime.tzinfo is None:
                    end_datetime = local_tz.localize(end_datetime)
                return end_datetime
                
        except Exception as e:
            logger.warning(f"Failed to parse end_date: {e}")
            return None
