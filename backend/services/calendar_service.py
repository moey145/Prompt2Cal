import os
import json
import logging
import re
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from uuid import uuid4

from ..models.event_models import ParsedEvent

load_dotenv()

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        # Use absolute paths for credentials files
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.CREDENTIALS_FILE = os.path.join(self.BASE_DIR, 'credentials.json')
        self.TOKEN_FILE = os.path.join(self.BASE_DIR, 'token.json')
        self.service = None
        
        # Load OAuth client credentials from environment variables
        self.CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
        self.CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
        self.REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')
        
        # Fallback to credentials.json if env vars not set (for backward compatibility)
        if not self.CLIENT_ID or not self.CLIENT_SECRET:
            if os.path.exists(self.CREDENTIALS_FILE):
                try:
                    with open(self.CREDENTIALS_FILE, 'r') as f:
                        creds_data = json.load(f)
                        if 'installed' in creds_data:
                            creds_data = creds_data['installed']
                        elif 'web' in creds_data:
                            creds_data = creds_data['web']
                        self.CLIENT_ID = creds_data.get('client_id')
                        self.CLIENT_SECRET = creds_data.get('client_secret')
                        if not self.REDIRECT_URI and 'redirect_uris' in creds_data and creds_data['redirect_uris']:
                            self.REDIRECT_URI = creds_data['redirect_uris'][0]
                except Exception as e:
                    logger.warning(f"Could not load credentials from file: {e}")
        
        self._load_credentials()
    
    def _load_credentials(self):
        """Load or create credentials for Google Calendar API."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)
            except (ValueError, Exception) as e:
                logger.warning(f"Invalid or corrupted token file: {str(e)}")
                logger.info("Removing invalid token file and will require re-authentication")
                # Remove the invalid token file
                try:
                    os.remove(self.TOKEN_FILE)
                except Exception as remove_error:
                    logger.error(f"Could not remove invalid token file: {str(remove_error)}")
                creds = None
        
        # If there are no valid credentials, we need to authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed credentials
                    with open(self.TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.warning(f"Could not refresh credentials: {str(e)}")
                    creds = None
            else:
                # Check if credentials.json exists
                if not os.path.exists(self.CREDENTIALS_FILE):
                    logger.warning(f"Google credentials file not found at {self.CREDENTIALS_FILE}")
                    logger.info("Google Calendar integration will not be available until credentials are set up")
                    return
                
                logger.info("No valid credentials found. Google Calendar authentication required.")
                # For now, we'll handle auth in the auth endpoints
                return
        
        # Build the service only if we have valid credentials
        if creds:
            try:
                self.service = build('calendar', 'v3', credentials=creds)
                logger.info("Google Calendar service initialized successfully")
            except Exception as e:
                logger.error(f"Error building Calendar service: {str(e)}")
                self.service = None
    
    async def get_auth_url(self, user_id: Optional[str] = None) -> str:
        """Get the Google OAuth2 authorization URL."""
        if not self.CLIENT_ID or not self.CLIENT_SECRET:
            raise Exception("Google OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env file")
        
        # Create client config from environment variables
        client_config = {
            "web": {
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.REDIRECT_URI]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            self.SCOPES,
            redirect_uri=self.REDIRECT_URI
        )
        
        # Add user_id to state to persist it through OAuth flow
        state = user_id if user_id else ""
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # Force consent screen to get refresh token
            state=state
        )
        
        return auth_url
    
    async def handle_auth_callback(self, code: str, user_id: Optional[str] = None):
        """Handle the OAuth2 callback and save credentials."""
        if not self.CLIENT_ID or not self.CLIENT_SECRET:
            raise Exception("Google OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env file")
        
        # Create client config from environment variables
        client_config = {
            "web": {
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.REDIRECT_URI]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            self.SCOPES,
            redirect_uri=self.REDIRECT_URI
        )
        
        # Exchange code for credentials
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Determine token file path based on user_id
        if user_id:
            user_tokens_dir = os.path.join(self.BASE_DIR, 'user_tokens')
            os.makedirs(user_tokens_dir, exist_ok=True)
            token_file = os.path.join(user_tokens_dir, f'{user_id}.json')
        else:
            token_file = self.TOKEN_FILE
        
        # Save only user-specific tokens (without client_id/secret)
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "scopes": creds.scopes,
            "expiry": creds.expiry.isoformat() if creds.expiry else None
        }
        
        with open(token_file, 'w') as token:
            json.dump(token_data, token)
        
        logger.info(f"Google Calendar authentication completed successfully for user: {user_id}")
        
        # Reinitialize service with new credentials
        self.service = build('calendar', 'v3', credentials=creds)
    
    def _load_user_credentials(self, user_id: Optional[str] = None):
        """Load credentials for a specific user."""
        if user_id:
            user_tokens_dir = os.path.join(self.BASE_DIR, 'user_tokens')
            token_file = os.path.join(user_tokens_dir, f'{user_id}.json')
            if os.path.exists(token_file):
                try:
                    # Load user token data (without client credentials)
                    with open(token_file, 'r') as f:
                        token_data = json.load(f)
                    
                    # Reconstruct credentials with client_id/secret from env
                    if not self.CLIENT_ID or not self.CLIENT_SECRET:
                        logger.error("Cannot load user credentials: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")
                        return False
                    
                    # Handle both old format (with client_id/secret) and new format (without)
                    if 'client_id' in token_data:
                        # Old format - use as-is but update from env if available
                        creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
                    else:
                        # New format - reconstruct credentials
                        from datetime import datetime as dt
                        expiry = None
                        if token_data.get('expiry'):
                            expiry = dt.fromisoformat(token_data['expiry'])
                        
                        creds = Credentials(
                            token=token_data.get('token'),
                            refresh_token=token_data.get('refresh_token'),
                            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                            client_id=self.CLIENT_ID,
                            client_secret=self.CLIENT_SECRET,
                            scopes=token_data.get('scopes', self.SCOPES),
                            expiry=expiry
                        )
                    
                    if creds and creds.valid:
                        self.service = build('calendar', 'v3', credentials=creds)
                        return True
                    elif creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        # Save refreshed token (without client credentials)
                        token_data = {
                            "token": creds.token,
                            "refresh_token": creds.refresh_token,
                            "token_uri": creds.token_uri,
                            "scopes": creds.scopes,
                            "expiry": creds.expiry.isoformat() if creds.expiry else None
                        }
                        with open(token_file, 'w') as token:
                            json.dump(token_data, token)
                        self.service = build('calendar', 'v3', credentials=creds)
                        return True
                except Exception as e:
                    logger.error(f"Error loading user credentials: {e}")
                    return False
        return False
    
    async def get_calendars(self, user_id: Optional[str] = None, writable_only: bool = True) -> List[Dict]:
        """
        Get list of user's calendars.
        Returns list of calendars with id, summary, primary flag, and accessRole.
        
        Args:
            user_id: Optional user ID to load credentials for
            writable_only: If True, only return calendars where user has write access (writer/owner)
        """
        if user_id:
            self._load_user_credentials(user_id)
        
        if not self.service:
            raise Exception("Google Calendar service not initialized. Please authenticate first.")
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = []
            for calendar in calendar_list.get('items', []):
                access_role = calendar.get('accessRole', 'reader')
                
                # Filter out read-only calendars if writable_only is True
                if writable_only and access_role not in ['writer', 'owner']:
                    continue
                
                calendars.append({
                    'id': calendar['id'],
                    'summary': calendar.get('summary', 'Untitled Calendar'),
                    'primary': calendar.get('primary', False),
                    'accessRole': access_role
                })
            # Sort: primary first, then by name
            calendars.sort(key=lambda x: (not x['primary'], x['summary'].lower()))
            return calendars
        except HttpError as error:
            logger.error(f"Error fetching calendars: {error}")
            raise Exception(f"Failed to fetch calendars: {str(error)}")
    
    async def create_calendar_event(self, parsed_event: ParsedEvent, user_id: Optional[str] = None, original_text: Optional[str] = None, calendar_id: Optional[str] = None) -> str:
        """
        Create an event in Google Calendar and return the event link.
        """
        # Prefer the original_text parameter, but fall back to the event payload if not supplied
        if original_text is None:
            original_text = getattr(parsed_event, "original_text", None)
        
        # Load user-specific credentials if user_id is provided
        if user_id:
            self._load_user_credentials(user_id)
        
        if not self.service:
            raise Exception("Google Calendar service not initialized. Please authenticate first.")
        
        # Validate parsed event data
        if not parsed_event.title:
            raise Exception("Event title is required")
        if not parsed_event.start_time or not parsed_event.end_time:
            raise Exception("Event start and end times are required")
        
        try:
            # Convert ISO strings to datetime objects
            # Handle both timezone-aware and naive datetime strings
            if 'T' in parsed_event.start_time and '+' in parsed_event.start_time:
                # Already timezone-aware
                start_datetime = datetime.fromisoformat(parsed_event.start_time.replace('Z', '+00:00'))
                end_datetime = datetime.fromisoformat(parsed_event.end_time.replace('Z', '+00:00'))
            else:
                # Naive datetime, assume local time
                start_datetime = datetime.fromisoformat(parsed_event.start_time)
                end_datetime = datetime.fromisoformat(parsed_event.end_time)
            
            # Create event body
            # Use the timezone from the datetime objects
            event_body = {
                'summary': parsed_event.title,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': str(start_datetime.tzinfo) if start_datetime.tzinfo else 'America/New_York',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': str(end_datetime.tzinfo) if end_datetime.tzinfo else 'America/New_York',
                },
            }
            
            # Add optional fields
            if parsed_event.location:
                event_body['location'] = parsed_event.location
            
            if parsed_event.notes:
                event_body['description'] = parsed_event.notes

            # Add attendees if provided
            if getattr(parsed_event, "attendees", None):
                attendees_list = []
                seen_emails = set()
                for attendee in parsed_event.attendees:
                    if not attendee:
                        continue
                    email = attendee.strip()
                    if not email:
                        continue
                    email_lower = email.lower()
                    if email_lower in seen_emails:
                        continue
                    attendees_list.append({'email': email})
                    seen_emails.add(email_lower)
                if attendees_list:
                    event_body['attendees'] = attendees_list

            # Add Google Meet conference data if requested
            if getattr(parsed_event, "add_conference", False):
                event_body['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"prompt2cal-{uuid4().hex}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'},
                    }
                }

            # Add color if specified (only use Google Calendar predefined colors)
            if parsed_event.color:
                color_id = self._get_google_color_id(parsed_event.color)
                if color_id:
                    event_body['colorId'] = color_id
            
            # Add reminders if specified
            if parsed_event.reminder and parsed_event.reminder != "none":
                try:
                    reminder_minutes = int(parsed_event.reminder)
                    event_body['reminders'] = {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': reminder_minutes}
                        ]
                    }
                except ValueError:
                    logger.warning(f"Invalid reminder value: {parsed_event.reminder}")
            
            # Add recurrence if specified
            recurrence_rule = self._build_recurrence_rule(parsed_event, original_text)
            if recurrence_rule:
                event_body['recurrence'] = recurrence_rule
                logger.info(f"Adding recurrence rule: {recurrence_rule}")
            
            # Create the main event
            insert_kwargs = {
                'calendarId': calendar_id or 'primary',
                'body': event_body,
            }
            if 'conferenceData' in event_body:
                insert_kwargs['conferenceDataVersion'] = 1

            event = self.service.events().insert(**insert_kwargs).execute()
            
            # Create buffer events if specified
            buffer_events = []
            if parsed_event.buffer_before and parsed_event.buffer_before > 0:
                buffer_start = start_datetime - timedelta(minutes=parsed_event.buffer_before)
                buffer_end = start_datetime
                buffer_event_body = {
                    'summary': f"🕐 {parsed_event.title} (Buffer)",
                    'start': {
                        'dateTime': buffer_start.isoformat(),
                        'timeZone': str(buffer_start.tzinfo) if buffer_start.tzinfo else 'America/New_York',
                    },
                    'end': {
                        'dateTime': buffer_end.isoformat(),
                        'timeZone': str(buffer_end.tzinfo) if buffer_end.tzinfo else 'America/New_York',
                    },
                    'colorId': '8',  # Blue Grey for buffer events
                }
                buffer_event = self.service.events().insert(
                    calendarId=calendar_id or 'primary',
                    body=buffer_event_body
                ).execute()
                buffer_events.append(buffer_event)
                logger.info(f"Buffer before event created: {buffer_event.get('id')}")
            
            if parsed_event.buffer_after and parsed_event.buffer_after > 0:
                buffer_start = end_datetime
                buffer_end = end_datetime + timedelta(minutes=parsed_event.buffer_after)
                buffer_event_body = {
                    'summary': f"🕐 {parsed_event.title} (Buffer)",
                    'start': {
                        'dateTime': buffer_start.isoformat(),
                        'timeZone': str(buffer_start.tzinfo) if buffer_start.tzinfo else 'America/New_York',
                    },
                    'end': {
                        'dateTime': buffer_end.isoformat(),
                        'timeZone': str(buffer_end.tzinfo) if buffer_end.tzinfo else 'America/New_York',
                    },
                    'colorId': '8',  # Blue Grey for buffer events
                }
                buffer_event = self.service.events().insert(
                    calendarId=calendar_id or 'primary',
                    body=buffer_event_body
                ).execute()
                buffer_events.append(buffer_event)
                logger.info(f"Buffer after event created: {buffer_event.get('id')}")
            
            # Return the main event link
            event_link = event.get('htmlLink', '')
            logger.info(f"Event created successfully: {event.get('id')}")
            
            return event_link
            
        except HttpError as e:
            error_message = str(e)
            error_reason = None
            
            # Check for permission errors (403 Forbidden)
            if e.resp.status == 403:
                # Try to extract error details from the error content
                try:
                    error_content = e.content.decode('utf-8') if e.content else '{}'
                    import json
                    error_data = json.loads(error_content)
                    error_info = error_data.get('error', {})
                    
                    # Check error reason
                    if 'errors' in error_info:
                        for error_detail in error_info['errors']:
                            reason = error_detail.get('reason', '')
                            if reason == 'requiredAccessLevel':
                                calendar_name = calendar_id or 'primary'
                                error_message = f"You don't have write access to the calendar '{calendar_name}'. Please select a calendar where you have writer or owner permissions, or use your primary calendar."
                                logger.error(f"Permission denied: Calendar '{calendar_name}' is read-only. User needs writer/owner access.")
                                raise Exception(error_message)
                            error_reason = reason
                except (json.JSONDecodeError, AttributeError, KeyError) as parse_error:
                    # If we can't parse the error, check the error message string
                    if 'requiredAccessLevel' in error_message or 'writer access' in error_message.lower():
                        calendar_name = calendar_id or 'primary'
                        error_message = f"You don't have write access to the calendar '{calendar_name}'. Please select a calendar where you have writer or owner permissions."
                        logger.error(f"Permission denied: Calendar '{calendar_name}' is read-only.")
                        raise Exception(error_message)
            
            logger.error(f"Google Calendar API error: {error_message}")
            raise Exception(f"Failed to create calendar event: {error_message}")
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise Exception(f"Failed to create calendar event: {str(e)}")
    
    def _build_recurrence_rule(self, parsed_event: ParsedEvent, original_text: Optional[str] = None) -> List[str]:
        """Build RRULE for Google Calendar recurring events."""
        # Check if this is a recurring event
        if not parsed_event.recurrence_type or parsed_event.recurrence_type == "none":
            return None
        
        recurrence_type_str = (
            parsed_event.recurrence_type.value 
            if hasattr(parsed_event.recurrence_type, 'value')
            else str(parsed_event.recurrence_type or '').lower()
        )
        
        if recurrence_type_str == "none":
            return None
        
        # Build RRULE based on recurrence type
        interval = parsed_event.recurrence_interval or 1
        freq_map = {
            "daily": "DAILY",
            "weekly": "WEEKLY",
            "monthly": "MONTHLY",
            "yearly": "YEARLY"
        }
        freq = freq_map.get(recurrence_type_str, "WEEKLY")
        
        # Start building RRULE
        rrule_parts = [f"FREQ={freq}", f"INTERVAL={interval}"]
        
        # Check if this is a weekend or weekday event (for weekly/daily recurrence)
        is_weekend_event = False
        is_weekday_event = False
        if recurrence_type_str in {"weekly", "daily"}:
            text_sources = []
            if original_text:
                text_sources.append(original_text)
            if getattr(parsed_event, "title", None):
                text_sources.append(parsed_event.title)
            if getattr(parsed_event, "notes", None):
                text_sources.append(parsed_event.notes)
            combined_text = " ".join(text_sources).lower()

            has_weekend_keyword = bool(re.search(r"\bweekend(s)?\b", combined_text))
            has_weekday_keyword = bool(re.search(r"\b(weekdays?|business\s+days?|workdays?|work\s+days?)\b", combined_text))

            start_weekday = None
            try:
                if parsed_event.start_time:
                    start_weekday = datetime.fromisoformat(parsed_event.start_time).weekday()
            except Exception:
                start_weekday = None

            if has_weekend_keyword and (start_weekday is None or start_weekday in (5, 6)):
                is_weekend_event = True
            elif has_weekday_keyword:
                is_weekday_event = True

        # Add BYDAY for weekend events (both Saturday and Sunday)
        if is_weekend_event and "BYDAY=" not in ";".join(rrule_parts):
            rrule_parts.append("BYDAY=SA,SU")
        # Add BYDAY for weekday events (Monday through Friday)
        if is_weekday_event and "BYDAY=" not in ";".join(rrule_parts):
            rrule_parts.append("BYDAY=MO,TU,WE,TH,FR")
        
        # Add COUNT if specified
        if parsed_event.recurrence_count:
            rrule_parts.append(f"COUNT={parsed_event.recurrence_count}")
        elif parsed_event.end_after_count:
            rrule_parts.append(f"COUNT={parsed_event.end_after_count}")
        # If no count specified and no end_date, it's indefinite (no COUNT or UNTIL)
        
        # Add UNTIL if end_date is specified
        if parsed_event.end_date:
            from .date_parser import DateParser
            date_parser = DateParser()
            import pytz
            local_tz = pytz.timezone('UTC')  # Default timezone
            end_datetime = date_parser.parse_end_date(parsed_event.end_date, local_tz)
            if end_datetime:
                # Google Calendar uses UTC date strings in YYYYMMDDTHHMMSSZ format
                until_str = end_datetime.strftime("%Y%m%dT%H%M%SZ")
                rrule_parts.append(f"UNTIL={until_str}")
        
        # Build the complete RRULE string
        rrule = "RRULE:" + ";".join(rrule_parts)
        
        return [rrule]
    
    def _get_google_color_id(self, hex_color: str) -> str:
        """Convert hex color to Google Calendar colorId if it matches a predefined color."""
        # Google Calendar predefined colors - only the 8 colors we support in the UI
        color_mapping = {
            '#4285f4': '1',  # Blue
            '#ea4335': '2',  # Red  
            '#fbbc04': '3',  # Yellow
            '#34a853': '4',  # Green
            '#9c27b0': '5',  # Purple
            '#ff9800': '6',  # Orange
            '#795548': '7',  # Brown
            '#607d8b': '8',  # Blue Grey
        }
        
        # Normalize hex color (remove # if present, convert to lowercase)
        normalized_color = hex_color.lower().lstrip('#')
        if len(normalized_color) == 6:
            normalized_color = '#' + normalized_color
        
        return color_mapping.get(normalized_color, None)

    async def get_events_in_range(self, start_time: datetime, end_time: datetime, calendar_id: Optional[str] = None) -> List[Dict]:
        """
        Get all events in a specific time range from Google Calendar.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            calendar_id: Optional calendar ID (defaults to 'primary')
        """
        if not self.service:
            raise Exception("Google Calendar service not initialized. Please authenticate first.")
        
        try:
            # Convert to RFC3339 format for Google Calendar API
            time_min = start_time.isoformat() + 'Z' if start_time.tzinfo is None else start_time.isoformat()
            time_max = end_time.isoformat() + 'Z' if end_time.tzinfo is None else end_time.isoformat()
            
            events_result = self.service.events().list(
                calendarId=calendar_id or 'primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Found {len(events)} events in range {time_min} to {time_max}")
            return events
            
        except HttpError as e:
            logger.error(f"Google Calendar API error getting events: {str(e)}")
            raise Exception(f"Failed to get calendar events: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting calendar events: {str(e)}")
            raise Exception(f"Failed to get calendar events: {str(e)}")

    async def find_available_slots(self, duration_minutes: int, start_date: datetime, end_date: datetime, 
                                 working_hours: tuple = (9, 17), buffer_minutes: int = 15) -> List[Dict]:
        """
        Find available time slots for a meeting of specified duration.
        
        Args:
            duration_minutes: Duration of the meeting in minutes
            start_date: Start of search range
            end_date: End of search range
            working_hours: Tuple of (start_hour, end_hour) for working hours
            buffer_minutes: Buffer time around meetings
        """
        try:
            # Get existing events in the range
            existing_events = await self.get_events_in_range(start_date, end_date)
            
            # Parse existing events into time blocks
            busy_blocks = []
            for event in existing_events:
                start = event.get('start', {})
                end = event.get('end', {})
                
                # Handle both dateTime and date formats
                if 'dateTime' in start:
                    event_start = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                elif 'date' in start:
                    # All-day event
                    event_start = datetime.fromisoformat(start['date'] + 'T00:00:00')
                    event_end = datetime.fromisoformat(end['date'] + 'T23:59:59')
                else:
                    continue
                
                # Add buffer time
                event_start = event_start - timedelta(minutes=buffer_minutes)
                event_end = event_end + timedelta(minutes=buffer_minutes)
                
                busy_blocks.append((event_start, event_end))
            
            # Sort busy blocks by start time
            busy_blocks.sort(key=lambda x: x[0])
            
            # Find available slots
            available_slots = []
            current_time = start_date.replace(hour=working_hours[0], minute=0, second=0, microsecond=0)
            end_time = end_date.replace(hour=working_hours[1], minute=0, second=0, microsecond=0)
            
            while current_time < end_time:
                # Skip weekends
                if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    current_time = current_time.replace(hour=working_hours[0], minute=0) + timedelta(days=1)
                    continue
                
                # Check if current time is within working hours
                if current_time.hour < working_hours[0] or current_time.hour >= working_hours[1]:
                    current_time = current_time.replace(hour=working_hours[0], minute=0) + timedelta(days=1)
                    continue
                
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any busy block
                conflicts = False
                for busy_start, busy_end in busy_blocks:
                    if (current_time < busy_end and slot_end > busy_start):
                        conflicts = True
                        # Move to after this busy block
                        current_time = busy_end
                        break
                
                if not conflicts:
                    available_slots.append({
                        'start': current_time.isoformat(),
                        'end': slot_end.isoformat(),
                        'duration_minutes': duration_minutes,
                        'formatted_time': current_time.strftime('%A, %B %d at %I:%M %p')
                    })
                    current_time += timedelta(minutes=30)  # Check every 30 minutes
                else:
                    current_time += timedelta(minutes=15)  # Check every 15 minutes if conflicted
            
            logger.info(f"Found {len(available_slots)} available slots")
            return available_slots
            
        except Exception as e:
            logger.error(f"Error finding available slots: {str(e)}")
            raise Exception(f"Failed to find available slots: {str(e)}")

    async def check_conflicts(self, start_time: datetime, end_time: datetime, buffer_minutes: int = 15, calendar_id: Optional[str] = None, recurrence_type: Optional[str] = None, recurrence_count: Optional[int] = None, recurrence_interval: int = 1, end_date: Optional[str] = None) -> List[Dict]:
        """
        Check if a proposed meeting time conflicts with existing events.
        For recurring events, checks conflicts for multiple future occurrences.
        
        Args:
            start_time: Proposed meeting start time
            end_time: Proposed meeting end time
            buffer_minutes: Buffer time around meetings
            calendar_id: Optional calendar ID (defaults to 'primary')
            recurrence_type: Optional recurrence type ('daily', 'weekly', 'monthly', 'yearly')
            recurrence_count: Optional number of occurrences to check (defaults to 10 for recurring events)
            recurrence_interval: Interval between occurrences (defaults to 1)
            end_date: Optional end date for recurring events
        """
        try:
            # Determine how many occurrences to check
            occurrences_to_check = 1
            if recurrence_type and recurrence_type.lower() != "none":
                # For recurring events, check next 10 occurrences (or until end_date if specified)
                if recurrence_count:
                    occurrences_to_check = min(recurrence_count, 10)  # Cap at 10 for performance
                else:
                    occurrences_to_check = 10  # Default to 10 for indefinite recurring events
                
                # If end_date is specified, calculate how many occurrences until then
                if end_date:
                    try:
                        from dateutil import parser as date_parser
                        end_datetime = date_parser.parse(end_date)
                        if end_datetime:
                            # Calculate approximate occurrences until end_date
                            duration = end_time - start_time
                            if recurrence_type.lower() == "daily":
                                days_diff = (end_datetime - start_time).days
                                occurrences_to_check = min(days_diff + 1, 30)  # Cap at 30 days
                            elif recurrence_type.lower() == "weekly":
                                weeks_diff = (end_datetime - start_time).days // 7
                                occurrences_to_check = min(weeks_diff + 1, 12)  # Cap at 12 weeks
                            elif recurrence_type.lower() == "monthly":
                                months_diff = (end_datetime.year - start_time.year) * 12 + (end_datetime.month - start_time.month)
                                occurrences_to_check = min(months_diff + 1, 12)  # Cap at 12 months
                            elif recurrence_type.lower() == "yearly":
                                years_diff = end_datetime.year - start_time.year
                                occurrences_to_check = min(years_diff + 1, 5)  # Cap at 5 years
                    except Exception as e:
                        logger.warning(f"Could not parse end_date for conflict checking: {e}")
                        occurrences_to_check = 10
            
            # Generate all occurrences to check
            occurrences = []
            current_start = start_time
            current_end = end_time
            duration = end_time - start_time
            
            for i in range(occurrences_to_check):
                occurrences.append((current_start, current_end))
                
                # Calculate next occurrence based on recurrence type
                if recurrence_type and recurrence_type.lower() != "none" and i < occurrences_to_check - 1:
                    if recurrence_type.lower() == "daily":
                        current_start = current_start + timedelta(days=recurrence_interval)
                    elif recurrence_type.lower() == "weekly":
                        current_start = current_start + timedelta(weeks=recurrence_interval)
                    elif recurrence_type.lower() == "monthly":
                        # Add months (approximate)
                        from dateutil.relativedelta import relativedelta
                        current_start = current_start + relativedelta(months=recurrence_interval)
                    elif recurrence_type.lower() == "yearly":
                        from dateutil.relativedelta import relativedelta
                        current_start = current_start + relativedelta(years=recurrence_interval)
                    else:
                        break  # Unknown recurrence type, stop
                    
                    current_end = current_start + duration
                    
                    # Stop if we've passed end_date
                    if end_date:
                        try:
                            from dateutil import parser as date_parser
                            end_datetime = date_parser.parse(end_date)
                            if end_datetime and current_start > end_datetime:
                                break
                        except:
                            pass
            
            # Get the time range covering all occurrences
            if occurrences:
                min_start = min(occ[0] for occ in occurrences)
                max_end = max(occ[1] for occ in occurrences)
                buffered_start = min_start - timedelta(minutes=buffer_minutes)
                buffered_end = max_end + timedelta(minutes=buffer_minutes)
            else:
                buffered_start = start_time - timedelta(minutes=buffer_minutes)
                buffered_end = end_time + timedelta(minutes=buffer_minutes)
            
            # Get events in the buffered range
            existing_events = await self.get_events_in_range(buffered_start, buffered_end, calendar_id=calendar_id)
            
            conflicts = []
            recurring_event_groups = {}  # Map of recurringEventId to list of conflicts
            
            for occurrence_start, occurrence_end in occurrences:
                for event in existing_events:
                    event_start = event.get('start', {})
                    event_end = event.get('end', {})
                    
                    # Handle both dateTime and date formats
                    if 'dateTime' in event_start:
                        evt_start = datetime.fromisoformat(event_start['dateTime'].replace('Z', '+00:00'))
                        evt_end = datetime.fromisoformat(event_end['dateTime'].replace('Z', '+00:00'))
                    elif 'date' in event_start:
                        # All-day event
                        evt_start = datetime.fromisoformat(event_start['date'] + 'T00:00:00')
                        evt_end = datetime.fromisoformat(event_end['date'] + 'T23:59:59')
                    else:
                        continue
                    
                    # Check for overlap with this occurrence
                    if (occurrence_start < evt_end and occurrence_end > evt_start):
                        # Check if this is a recurring event occurrence
                        recurring_event_id = event.get('recurringEventId')
                        
                        if recurring_event_id:
                            # This is an occurrence of a recurring event
                            if recurring_event_id not in recurring_event_groups:
                                recurring_event_groups[recurring_event_id] = {
                                    'title': event.get('summary', 'Untitled Event'),
                                    'location': event.get('location', ''),
                                    'recurring_event_id': recurring_event_id,
                                    'is_recurring': True,
                                    'occurrence_count': 0,
                                    'first_occurrence_start': evt_start.isoformat(),
                                    'first_occurrence_end': evt_end.isoformat(),
                                    'last_occurrence_start': evt_start.isoformat(),
                                    'last_occurrence_end': evt_end.isoformat()
                                }
                            
                            # Update occurrence count and date range
                            recurring_event_groups[recurring_event_id]['occurrence_count'] += 1
                            
                            # Compare dates properly
                            first_start = datetime.fromisoformat(recurring_event_groups[recurring_event_id]['first_occurrence_start'].replace('Z', '+00:00') if 'Z' in recurring_event_groups[recurring_event_id]['first_occurrence_start'] else recurring_event_groups[recurring_event_id]['first_occurrence_start'])
                            last_start = datetime.fromisoformat(recurring_event_groups[recurring_event_id]['last_occurrence_start'].replace('Z', '+00:00') if 'Z' in recurring_event_groups[recurring_event_id]['last_occurrence_start'] else recurring_event_groups[recurring_event_id]['last_occurrence_start'])
                            
                            if evt_start < first_start:
                                recurring_event_groups[recurring_event_id]['first_occurrence_start'] = evt_start.isoformat()
                                recurring_event_groups[recurring_event_id]['first_occurrence_end'] = evt_end.isoformat()
                            if evt_start > last_start:
                                recurring_event_groups[recurring_event_id]['last_occurrence_start'] = evt_start.isoformat()
                                recurring_event_groups[recurring_event_id]['last_occurrence_end'] = evt_end.isoformat()
                        else:
                            # Single event (not recurring)
                            conflicts.append({
                                'title': event.get('summary', 'Untitled Event'),
                                'start': evt_start.isoformat(),
                                'end': evt_end.isoformat(),
                                'location': event.get('location', ''),
                                'conflict_type': 'overlap',
                                'is_recurring': False,
                                'occurrence_start': occurrence_start.isoformat(),
                                'occurrence_end': occurrence_end.isoformat()
                            })
            
            # Add grouped recurring events to conflicts
            for recurring_event_id, group in recurring_event_groups.items():
                conflicts.append({
                    'title': group['title'],
                    'start': group['first_occurrence_start'],
                    'end': group['first_occurrence_end'],
                    'location': group['location'],
                    'conflict_type': 'overlap',
                    'is_recurring': True,
                    'recurring_event_id': recurring_event_id,
                    'occurrence_count': group['occurrence_count'],
                    'last_occurrence_start': group['last_occurrence_start'],
                    'last_occurrence_end': group['last_occurrence_end']
                })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error checking conflicts: {str(e)}")
            raise Exception(f"Failed to check conflicts: {str(e)}")
    
    async def find_alternative_times(self, start_time: datetime, end_time: datetime, duration_minutes: int, 
                                     search_window_hours: int = 24, calendar_id: Optional[str] = None) -> List[Dict]:
        """
        Find alternative available time slots near the proposed time.
        
        Args:
            start_time: Proposed meeting start time
            end_time: Proposed meeting end time
            duration_minutes: Duration of the meeting
            search_window_hours: How many hours before/after to search (default 24)
            calendar_id: Optional calendar ID (defaults to 'primary')
        """
        try:
            # Search window: from (start_time - search_window_hours) to (start_time + search_window_hours)
            search_start = start_time - timedelta(hours=search_window_hours)
            search_end = start_time + timedelta(hours=search_window_hours)
            
            # Get all events in the search window
            existing_events = await self.get_events_in_range(search_start, search_end, calendar_id=calendar_id)
            
            # Build list of busy time blocks
            busy_blocks = []
            for event in existing_events:
                event_start = event.get('start', {})
                event_end = event.get('end', {})
                
                if 'dateTime' in event_start:
                    evt_start = datetime.fromisoformat(event_start['dateTime'].replace('Z', '+00:00'))
                    evt_end = datetime.fromisoformat(event_end['dateTime'].replace('Z', '+00:00'))
                    busy_blocks.append((evt_start, evt_end))
                elif 'date' in event_start:
                    # All-day event - skip for now
                    continue
            
            # Sort busy blocks by start time
            busy_blocks.sort(key=lambda x: x[0])
            
            # Find available slots
            alternatives = []
            current_time = search_start
            
            # Round to nearest 15 minutes
            current_time = current_time.replace(minute=(current_time.minute // 15) * 15, second=0, microsecond=0)
            
            while current_time + timedelta(minutes=duration_minutes) <= search_end:
                slot_start = current_time
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any busy block
                has_conflict = False
                for busy_start, busy_end in busy_blocks:
                    if (slot_start < busy_end and slot_end > busy_start):
                        has_conflict = True
                        # Skip to after this busy block
                        current_time = busy_end
                        # Round to nearest 15 minutes
                        current_time = current_time.replace(minute=((current_time.minute // 15) + 1) * 15, second=0, microsecond=0)
                        break
                
                if not has_conflict:
                    # Check if this slot is in the past
                    if slot_start > datetime.now(slot_start.tzinfo) if slot_start.tzinfo else datetime.now():
                        alternatives.append({
                            'start': slot_start.isoformat(),
                            'end': slot_end.isoformat(),
                            'formatted_start': slot_start.strftime('%A, %B %d at %I:%M %p'),
                            'formatted_time': f"{slot_start.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}",
                            'minutes_from_proposed': int((slot_start - start_time).total_seconds() / 60)
                        })
                    current_time += timedelta(minutes=15)
                
                # Limit to 5 alternatives
                if len(alternatives) >= 5:
                    break
            
            # Sort by proximity to proposed time
            alternatives.sort(key=lambda x: abs(x['minutes_from_proposed']))
            
            return alternatives[:5]  # Return top 5 alternatives
            
        except Exception as e:
            logger.error(f"Error finding alternative times: {str(e)}")
            raise Exception(f"Failed to find alternative times: {str(e)}")

    def is_authenticated(self, user_id: Optional[str] = None) -> bool:
        """Check if the service is authenticated and ready to use."""
        if user_id:
            # Check for user-specific token
            user_tokens_dir = os.path.join(self.BASE_DIR, 'user_tokens')
            token_file = os.path.join(user_tokens_dir, f'{user_id}.json')
            logger.info(f"Checking auth for user_id: {user_id}, token_file: {token_file}")
            
            if os.path.exists(token_file):
                try:
                    # Read token file manually to handle missing refresh_token
                    with open(token_file, 'r') as f:
                        token_data = json.load(f)
                    
                    logger.info(f"Token file contains keys: {list(token_data.keys())}")
                    
                    # Check if we have the basic auth info
                    if 'token' in token_data or 'access_token' in token_data:
                        logger.info("Token file exists and contains auth data - user is authenticated")
                        return True
                    else:
                        logger.warning("Token file exists but doesn't contain valid auth data")
                        return False
                except Exception as e:
                    logger.error(f"Error loading credentials: {e}")
                    return False
            else:
                logger.warning(f"Token file does not exist: {token_file}")
            return False
        else:
            # Check for global token
            return self.service is not None
    
    def logout(self, user_id: Optional[str] = None) -> bool:
        """
        Logout and clear user credentials.
        Returns True if token was successfully removed, False otherwise.
        """
        try:
            if user_id:
                # Remove user-specific token
                user_tokens_dir = os.path.join(self.BASE_DIR, 'user_tokens')
                token_file = os.path.join(user_tokens_dir, f'{user_id}.json')
                if os.path.exists(token_file):
                    os.remove(token_file)
                    logger.info(f"Removed token file for user: {user_id}")
                    return True
                else:
                    logger.warning(f"No token file found for user: {user_id}")
                    return False
            else:
                # Remove global token
                if os.path.exists(self.TOKEN_FILE):
                    os.remove(self.TOKEN_FILE)
                    self.service = None
                    logger.info("Removed global token file")
                    return True
                else:
                    logger.warning("No global token file found")
                    return False
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return False
