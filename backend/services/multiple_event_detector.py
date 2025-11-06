"""
Multiple event detection utilities.
Handles detection of whether input text contains multiple events.
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class MultipleEventDetector:
    """Handles detection of multiple events in input text."""
    
    def __init__(self):
        pass
    
    async def is_multiple_events(self, text: str) -> bool:
        """
        Determine if the input text describes multiple events.
        """
        try:
            indicators = [
                ' and ',  # "meeting at 8pm and lunch at 2pm"
                ' then ',  # "meeting at 8pm then lunch at 2pm"
                ' also ',  # "meeting at 8pm also lunch at 2pm"
                ' plus ',  # "meeting at 8pm plus lunch at 2pm"
            ]
            
            text_lower = text.lower()
            
            # Count explicit time tokens rather than loose substrings like 'am' inside 'appointment'
            time_tokens = re.findall(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", text_lower)
            time_count = len(time_tokens)
            
            # Check for time ranges (e.g., "9:00am - 11:30am") - these are single events
            time_range_pattern = r"\b\d{1,2}(:\d{2})?\s*(am|pm)\s*-\s*\d{1,2}(:\d{2})?\s*(am|pm)\b"
            has_time_range = bool(re.search(time_range_pattern, text_lower))
            
            # If it's a time range, reduce the time count to 1
            if has_time_range and time_count >= 2:
                time_count = 1
            
            # Check for multiple day indicators
            day_indicators = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'tomorrow', 'today']
            day_count = sum(text_lower.count(day) for day in day_indicators)
            
            # Debug logging
            logger.info(f"Multiple events check for: '{text}'")
            logger.info(f"Indicators found: {[ind for ind in indicators if ind in text_lower]}")
            logger.info(f"Time count: {time_count}, Day count: {day_count}")
            
            # Check for explicit separators first, but filter out "and" when it's part of duration/time descriptions
            has_separator = False
            for indicator in indicators:
                if indicator in text_lower:
                    # Special handling for "and" - check if it's part of duration/time description
                    if indicator == ' and ':
                        # Check if "and" is part of duration (e.g., "2 hours and 30 minutes", "2 and a half hours", "an hour and a half")
                        duration_and_patterns = [
                            r'\b\d+\s+(hours?|minutes?|days?|weeks?|months?)\s+and\s+\d+\s+(hours?|minutes?|days?|weeks?|months?)\b',  # "2 hours and 30 minutes"
                            r'\b\d+\s+and\s+(a\s+)?(half|quarter|third)\s+(hours?|minutes?|days?|weeks?|months?)\b',  # "2 and a half hours"
                            r'\b\d+\s+and\s+\d+\s+(hours?|minutes?|days?|weeks?|months?)\b',  # "2 and 30 hours"
                            r'\b(an?|one)\s+(hour|minute|day|week|month)\s+and\s+(a\s+)?(half|quarter|third)\b',  # "an hour and a half"
                            r'\b(an?|one)\s+(hour|minute|day|week|month)\s+and\s+\d+\s+(hours?|minutes?|days?|weeks?|months?)\b',  # "an hour and 30 minutes"
                        ]
                        
                        is_duration_and = any(re.search(pattern, text_lower) for pattern in duration_and_patterns)
                        if is_duration_and:
                            continue  # Skip this "and" as it's part of duration
                        
                        # Check if "and" is part of time description (e.g., "7pm and 8pm")
                        time_and_pattern = r'\b\d{1,2}(:\d{2})?\s*(am|pm)\s+and\s+\d{1,2}(:\d{2})?\s*(am|pm)\b'
                        if re.search(time_and_pattern, text_lower):
                            continue  # Skip this "and" as it's part of time range
                        
                        # Check if "and" is part of buffer time description (e.g., "30 minute buffer before and after", "15 minute before and after")
                        buffer_and_patterns = [
                            r'\b\d+\s+minute\s+buffer\s+(?:before|after)\s+and\s+(?:before|after)\b',
                            r'\b\d+\s+minute\s+(?:before|after)\s+and\s+(?:before|after)\b',
                            r'\b(?:before|after)\s+and\s+(?:before|after)\b',
                        ]
                        if any(re.search(pattern, text_lower) for pattern in buffer_and_patterns):
                            continue  # Skip this "and" as it's part of buffer description
                    
                    has_separator = True
                    break
            
            # Check for recurring patterns (strict)
            recurring_patterns = ['every day', 'every other', 'every ', 'daily', 'weekly', 'monthly', 'yearly', 'each month', 'each week', 'each day', 'first monday', 'first tuesday', 'first wednesday', 'first thursday', 'first friday', 'first saturday', 'first sunday']
            has_recurring = any(pattern in text_lower for pattern in recurring_patterns)

            # Phrases like 'next week', 'in 3 weeks' are single events, not multiple
            single_offset_week = bool(re.search(r"\b(next\s+week|in\s+\d+\s+weeks?)\b", text_lower))
            
            # Check for multiple distinct activities (lunch, dinner, meeting, etc.)
            activity_indicators = ['lunch', 'dinner', 'meeting', 'appointment', 'call', 'visit']
            activity_count = sum(text_lower.count(activity) for activity in activity_indicators)
            
            # Check for numbered events (e.g., "5 meetings", "3 appointments")
            number_pattern = r'\b(\d+)\s+(meetings?|appointments?|calls?|visits?)\b'
            number_match = re.search(number_pattern, text_lower)
            has_numbered_events = bool(number_match)
            
            logger.info(f"Number pattern match: {number_match.groups() if number_match else 'None'}")
            
            # If we have multiple indicators, likely multiple events
            is_multiple = (
                has_separator or
                time_count > 1 and (day_count > 0 or has_separator) or
                day_count > 1 or
                activity_count > 1 or
                has_numbered_events
            )
            
            # Recurring events are single events that get expanded later
            # Don't treat them as multiple events
            
            logger.info(f"Is multiple events: {is_multiple}")
            logger.info(f"Has separator: {has_separator}")
            logger.info(f"Has recurring: {has_recurring}")
            logger.info(f"Has numbered events: {has_numbered_events}")
            logger.info(f"Activity count: {activity_count}")
            
            return is_multiple
            
        except Exception as e:
            logger.error(f"Error in multiple events detection: {e}")
            return False
