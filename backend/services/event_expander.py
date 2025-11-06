"""
Event expansion utilities for recurring events.
Handles expanding single recurring events into multiple individual events.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import pytz

from ..models.event_models import ParsedEvent

logger = logging.getLogger(__name__)

class EventExpander:
    """Handles expansion of recurring events into multiple individual events."""
    
    def __init__(self):
        pass
    
    async def expand_single_recurring_event(
        self, 
        event: ParsedEvent, 
        tz_name: Optional[str] = None, 
        original_input: str = ""
    ) -> List[ParsedEvent]:
        """
        Expand a single ParsedEvent with recurrence information into multiple individual events.
        """
        try:
            if not event.recurrence_type or event.recurrence_type == "none":
                return [event]
            
            # Get timezone
            if tz_name:
                local_tz = pytz.timezone(tz_name)
            else:
                local_tz = pytz.timezone('UTC')
            
            # Parse the start time to get the first occurrence
            start_time_str = event.start_time
            if not start_time_str:
                return [event]
            
            # Parse the start time
            from .date_parser import DateParser
            date_parser = DateParser()
            start_datetime = date_parser.parse_start_time(start_time_str, local_tz)
            if not start_datetime:
                return [event]
            
            # Determine how many events to generate
            count = event.recurrence_count or 4  # Default to 4 occurrences
            
            # If end_date is provided, calculate count based on recurrence type
            if event.end_date and not event.recurrence_count:
                try:
                    end_datetime = date_parser.parse_end_date(event.end_date, local_tz)
                    
                    if end_datetime and start_datetime < end_datetime:
                        logger.info(f"Calculating count from {start_datetime.date()} to {end_datetime.date()}")
                        # Check if this is a weekday event first
                        is_weekday_event = (
                            "weekday" in str(event.start_time).lower() or 
                            "weekday" in str(event.title).lower() or
                            "weekday" in str(event.notes or "").lower() or
                            "weekday" in original_input.lower()
                        )
                        
                        if is_weekday_event:
                            # For "weekday" daily events, count only weekdays
                            weekdays_count = 0
                            current_date = start_datetime.date()
                            end_date = end_datetime.date()
                            while current_date <= end_date:
                                if current_date.weekday() < 5:  # Monday=0, Friday=4
                                    weekdays_count += 1
                                current_date += timedelta(days=1)
                            count = max(1, weekdays_count)
                            logger.info(f"Weekday count calculated: {count}")
                        elif event.recurrence_type == "daily":
                            count = max(1, (end_datetime.date() - start_datetime.date()).days)
                            logger.info(f"Daily count calculated: {count}")
                        elif event.recurrence_type == "weekly":
                            # For weekly events, count actual occurrences, not just weeks
                            count = 0
                            current_date = start_datetime.date()
                            end_date = end_datetime.date()
                            while current_date <= end_date:
                                count += 1
                                current_date += timedelta(weeks=1)
                            count = max(1, count)
                            logger.info(f"Weekly count calculated: {count}")
                        elif event.recurrence_type == "monthly":
                            count = max(1, (end_datetime.year - start_datetime.year) * 12 + (end_datetime.month - start_datetime.month))
                            logger.info(f"Monthly count calculated: {count}")
                        else:
                            count = max(1, (end_datetime.date() - start_datetime.date()).days)
                            logger.info(f"Default daily count calculated: {count}")
                    else:
                        logger.warning(f"Invalid end_date or end_date before start_date: {event.end_date}")
                        count = 4  # Fallback to default
                except Exception as e:
                    logger.warning(f"Failed to calculate count from end_date: {e}")
                    count = 4  # Fallback to default
            
            # Generate recurring events
            events = []
            current_date = start_datetime
            
            for i in range(count):
                # For weekday events, skip weekends during generation
                # Check both the start_time and the original input for "weekday"
                is_weekday_event = (
                    event.recurrence_type == "daily" and 
                    ("weekday" in str(event.start_time).lower() or 
                     "weekday" in str(event.title).lower() or
                     "weekday" in str(event.notes or "").lower() or
                     "weekday" in original_input.lower())
                )
                
                if is_weekday_event:
                    # Skip weekends - only add weekday events
                    while current_date.weekday() >= 5:  # Skip Saturday=5, Sunday=6
                        current_date += timedelta(days=1)
                
                end_time = current_date + timedelta(minutes=event.duration_minutes)
                
                recurring_event = ParsedEvent(
                    title=event.title,
                    start_time=current_date.isoformat(),
                    end_time=end_time.isoformat(),
                    duration_minutes=event.duration_minutes,
                    location=event.location,
                    notes=event.notes,
                    recurrence_type="none",  # Individual event, not recurring
                    recurrence_count=None,
                    recurrence_interval=1,
                    color=event.color,
                    reminder=event.reminder
                )
                events.append(recurring_event)
                
                # Move to next occurrence based on recurrence type
                if event.recurrence_type == "weekly":
                    current_date += timedelta(weeks=event.recurrence_interval)
                elif event.recurrence_type == "daily":
                    if is_weekday_event:
                        # For weekday events, move to next day and skip weekends
                        current_date += timedelta(days=1)
                        while current_date.weekday() >= 5:  # Skip Saturday=5, Sunday=6
                            current_date += timedelta(days=1)
                    else:
                        current_date += timedelta(days=event.recurrence_interval)
                elif event.recurrence_type == "monthly":
                    # Check if this is an ordinal monthly event (e.g., "first Monday of each month")
                    is_ordinal_monthly = any(ordinal in original_input.lower() for ordinal in ['first', 'second', 'third', 'fourth', 'last'])
                    
                    if is_ordinal_monthly:
                        # For ordinal monthly events, preserve the weekday and ordinal position
                        original_weekday = current_date.weekday()
                        
                        # Move to next month
                        if current_date.month == 12:
                            next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
                        else:
                            next_month = current_date.replace(month=current_date.month + 1, day=1)
                        
                        # Find the first occurrence of the target weekday in the next month
                        days_until_target = (original_weekday - next_month.weekday()) % 7
                        first_occurrence = next_month + timedelta(days=days_until_target)
                        
                        # Determine which week of the month we want
                        if 'first' in original_input.lower():
                            current_date = first_occurrence
                        elif 'second' in original_input.lower():
                            current_date = first_occurrence + timedelta(weeks=1)
                        elif 'third' in original_input.lower():
                            current_date = first_occurrence + timedelta(weeks=2)
                        elif 'fourth' in original_input.lower():
                            current_date = first_occurrence + timedelta(weeks=3)
                        elif 'last' in original_input.lower():
                            # Find the last occurrence of the weekday in the month
                            last_occurrence = first_occurrence
                            while (last_occurrence + timedelta(weeks=1)).month == next_month.month:
                                last_occurrence += timedelta(weeks=1)
                            current_date = last_occurrence
                        else:
                            current_date = first_occurrence
                    else:
                        # For regular monthly events, just add months
                        # Use relativedelta if available, otherwise approximate
                        try:
                            from dateutil.relativedelta import relativedelta
                            current_date = current_date + relativedelta(months=event.recurrence_interval)
                        except ImportError:
                            # Fallback: approximate month as 30 days
                            current_date += timedelta(days=30 * event.recurrence_interval)
                else:
                    # Default to weekly
                    current_date += timedelta(weeks=event.recurrence_interval)
            
            return events
            
        except Exception as e:
            logger.error(f"Error expanding single recurring event: {e}")
            return [event]
    
    def expand_recurring_events(self, text: str, tz_name: Optional[str] = None) -> List[ParsedEvent]:
        """
        Expand recurring events from text using regex patterns.
        This is a fallback method for simple recurring patterns.
        """
        try:
            import re
            from .date_parser import DateParser
            
            # Get timezone
            if tz_name:
                local_tz = pytz.timezone(tz_name)
            else:
                local_tz = pytz.timezone('UTC')
            
            date_parser = DateParser()
            
            # Clean and normalize input
            cleaned_text = text.lower().strip()
            
            # Pattern for weekly recurring events
            weekly_pattern = r'every\s+(tuesday|wednesday|thursday|friday|monday|saturday|sunday)\s+(.+?)\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)'
            weekly_match = re.search(weekly_pattern, cleaned_text)
            
            if weekly_match:
                day = weekly_match.group(1)
                title = weekly_match.group(2).strip()
                time_str = weekly_match.group(3)
                
                # Parse the time
                start_time = f"next {day} at {time_str}"
                start_datetime = date_parser.parse_start_time(start_time, local_tz)
                
                if start_datetime:
                    # Generate 4 weeks of events
                    events = []
                    current_date = start_datetime
                    
                    for i in range(4):
                        end_time = current_date + timedelta(minutes=60)  # Default 1 hour
                        
                        event = ParsedEvent(
                            title=title,
                            start_time=current_date.isoformat(),
                            end_time=end_time.isoformat(),
                            duration_minutes=60,
                            location=None,
                            notes=None,
                            recurrence_type="none",
                            recurrence_count=None,
                            recurrence_interval=1,
                            color=None,
                            reminder=None
                        )
                        events.append(event)
                        
                        # Move to next week
                        current_date += timedelta(weeks=1)
                    
                    return events
            
            return []
            
        except Exception as e:
            logger.error(f"Error expanding recurring events: {e}")
            return []
