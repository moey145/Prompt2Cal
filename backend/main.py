from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import logging

from backend.services.event_parser import EventParser
from backend.services.calendar_service import CalendarService
from backend.services.microsoft_calendar_service import MicrosoftCalendarService
from backend.services.confidence import attach_confidence
from backend.services import token_store
from backend.models.event_models import EventRequest, EventResponse, ParsedEvent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Prompt2Cal API",
    description="Convert natural language to calendar events",
    version="1.0.3"
)

# Configure CORS
# Get allowed origins from environment variable (comma-separated)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

# Add Chrome extension origin if provided
chrome_ext_id = os.getenv("CHROME_EXTENSION_ID")
if chrome_ext_id:
    allowed_origins.append(f"chrome-extension://{chrome_ext_id}")

# Chrome extensions each have a unique ID, so extension origins are matched by
# pattern rather than listed individually. This must be handled by CORSMiddleware
# itself: it is the outermost layer and answers preflight requests before any
# inner middleware runs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
event_parser = EventParser()
calendar_service = CalendarService()
microsoft_calendar_service = MicrosoftCalendarService()


def _normalize_provider(provider: Optional[str]) -> str:
    value = (provider or "google").strip().lower()
    return "microsoft" if value in {"microsoft", "outlook", "ms"} else "google"


def _calendar_service_for(provider: Optional[str]):
    return (
        microsoft_calendar_service
        if _normalize_provider(provider) == "microsoft"
        else calendar_service
    )


def _require_session(user_id: Optional[str]) -> None:
    """Reject calendar access without a session this server issued at sign-in."""
    if not token_store.is_valid_session(user_id):
        raise HTTPException(status_code=401, detail="Not signed in. Please connect your calendar.")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/auth/status")
async def auth_status(user_id: str = None, provider: str = None):
    """Check calendar authentication status for Google and/or Microsoft."""
    try:
        google_auth = calendar_service.is_authenticated(user_id=user_id)
        microsoft_auth = microsoft_calendar_service.is_authenticated(user_id=user_id)
        active = _normalize_provider(provider)
        authenticated = microsoft_auth if active == "microsoft" else google_auth
        # If no provider preference is given, authenticated means either is connected
        if provider is None:
            authenticated = google_auth or microsoft_auth
            if microsoft_auth and not google_auth:
                active = "microsoft"
            elif google_auth:
                active = "google"
        return {
            "authenticated": authenticated,
            "provider": active,
            "providers": {
                "google": google_auth,
                "microsoft": microsoft_auth,
            },
            "message": "Authenticated" if authenticated else "Not authenticated",
        }
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        return {
            "authenticated": False,
            "provider": _normalize_provider(provider),
            "providers": {"google": False, "microsoft": False},
            "message": f"Error: {str(e)}",
        }

@app.get("/calendars")
async def get_calendars(user_id: str = None, provider: str = None):
    """Get list of user's writable calendars for the active provider."""
    _require_session(user_id)
    active_provider = _normalize_provider(provider)
    service = _calendar_service_for(active_provider)
    try:
        calendars = await service.get_calendars(user_id=user_id, writable_only=True)
        for calendar in calendars:
            calendar.setdefault("provider", active_provider)
        return {
            "success": True,
            "provider": active_provider,
            "calendars": calendars,
        }
    except Exception as e:
        logger.error(f"Error fetching calendars: {str(e)}")
        return {
            "success": False,
            "provider": active_provider,
            "calendars": [],
            "message": f"Error: {str(e)}",
        }

@app.post("/create_event", response_model=EventResponse)
async def create_event(request: EventRequest):
    """
    Create a calendar event from natural language input.
    
    Process:
    1. Parse natural language into structured data
    2. Convert dates to ISO 8601 format
    3. Return parsed details for confirmation
    """
    try:
        logger.info(f"Processing event request: {request.text} (force_multiple: {request.force_multiple})")
        
        # If force_multiple is explicitly set (True or False), use that instead of detection
        if request.force_multiple is True:
            logger.info("Forcing multiple event parsing (user clicked Multiple Events button)")
            # Parse as multiple events
            is_multiple = True
        elif request.force_multiple is False:
            # For single event button (force_multiple=False), skip detection and parse as single
            logger.info("Parsing as single event (user clicked Single Event button)")
            is_multiple = False
        else:
            # Auto-detect when force_multiple is None
            logger.info("Auto-detecting single vs multiple events")
            is_multiple = await event_parser.is_multiple_events(request.text)
            logger.info(f"Auto-detection result: {'multiple' if is_multiple else 'single'}")
        
        if is_multiple:
            # Parse multiple events (with timezone)
            parsed_events = await event_parser.parse_multiple_events(request.text, tz_name=request.timezone)
            logger.info(f"Parsed {len(parsed_events)} events")
            
            # Check if we got expanded events OR a single recurring event that needs expansion
            if len(parsed_events) > 1:
                # Convert ParsedEvent objects to dicts for JSON serialization
                events_list = []
                for event in parsed_events:
                    if hasattr(event, 'model_dump'):
                        event_dict = event.model_dump()
                    elif isinstance(event, dict):
                        event_dict = dict(event)
                    else:
                        event_dict = event.dict() if hasattr(event, 'dict') else event.model_dump()
                    event_dict["original_text"] = request.text
                    if request.timezone:
                        event_dict["timezone"] = request.timezone
                    attach_confidence(event_dict, request.text, request.timezone)
                    events_list.append(event_dict)
                
                return JSONResponse(content={
                    "success": True,
                    "parsed_event": None,
                    "parsed_events": events_list,
                    "message": "",
                    "event_link": None,
                    "requires_confirmation": True,
                    "is_bulk": True
                })
            elif len(parsed_events) == 1:
                # A single recurring series (with or without end_date/count) must stay
                # one calendar event with an RRULE. Do not expand into a bulk list.
                single_event = parsed_events[0]
                recurrence_str = (
                    single_event.recurrence_type.value
                    if hasattr(single_event, 'recurrence_type') and hasattr(single_event.recurrence_type, 'value')
                    else str(getattr(single_event, 'recurrence_type', '') or '').lower()
                )
                if recurrence_str and recurrence_str != "none":
                    logger.info(
                        "Recurring series detected in multi path; keeping as one event "
                        f"(type={recurrence_str}, count={getattr(single_event, 'recurrence_count', None)}, "
                        f"end_date={getattr(single_event, 'end_date', None)})"
                    )
                else:
                    logger.info("Multiple events detected but only 1 event returned, falling back to single event")
        
        # Parse single event (with timezone passed in)
        parsed_event = await event_parser.parse_event_text(request.text, tz_name=request.timezone)

        # If user clicked Single Event button (force_multiple=False), NEVER expand
        # Always return exactly 1 event
        # Never expand a recurring series into a bulk list of one-offs.
        # Google / Microsoft create one series via RRULE (UNTIL/COUNT).
        recurrence_str = (
            parsed_event.recurrence_type.value
            if hasattr(parsed_event, 'recurrence_type') and hasattr(parsed_event.recurrence_type, 'value')
            else str(getattr(parsed_event, 'recurrence_type', '') or '').lower()
        )
        if recurrence_str and recurrence_str != "none":
            logger.info(
                "Recurring series kept as one event for calendar RRULE: "
                f"type={recurrence_str}, count={getattr(parsed_event, 'recurrence_count', None)}, "
                f"end_date={getattr(parsed_event, 'end_date', None)}"
            )

        # Convert to dict for response (check if it has model_dump method)
        if hasattr(parsed_event, 'model_dump'):
            event_dict = parsed_event.model_dump()
            logger.info(f"Converted ParsedEvent to dict: {type(event_dict)}")
        elif isinstance(parsed_event, dict):
            event_dict = parsed_event
            logger.info(f"Event already dict: {type(event_dict)}")
        else:
            # Fallback for older Pydantic versions
            event_dict = parsed_event.dict() if hasattr(parsed_event, 'dict') else dict(parsed_event)
            logger.info(f"Converted using fallback: {type(event_dict)}")
        
        # Attach original text for downstream processing
        event_dict["original_text"] = request.text
        if request.timezone:
            event_dict["timezone"] = request.timezone

        # Per-field source-grounding confidence for the preview UI
        attach_confidence(event_dict, request.text, request.timezone)

        # Return parsed details for confirmation
        return EventResponse(
            success=True,
            parsed_event=event_dict,
            message="",
            requires_confirmation=True
        )
        
    except Exception as e:
        logger.error(f"Error parsing event: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse event: {str(e)}")

@app.post("/confirm_event", response_model=EventResponse)
async def confirm_event(parsed_event: ParsedEvent, user_id: str = Query(None)):
    """
    Confirm and create the calendar event in Google or Microsoft Calendar.
    """
    _require_session(user_id)
    try:
        provider = _normalize_provider(getattr(parsed_event, "calendar_provider", None))
        logger.info(f"Confirming event: {parsed_event.title} via {provider}")

        service = _calendar_service_for(provider)
        event_link = await service.create_calendar_event(
            parsed_event,
            user_id=user_id,
            original_text=getattr(parsed_event, "original_text", None),
            calendar_id=getattr(parsed_event, "calendar_id", None)
        )
        
        # Convert to dict for response
        event_dict = parsed_event.model_dump() if hasattr(parsed_event, 'model_dump') else parsed_event.dict()
        
        return EventResponse(
            success=True,
            parsed_event=event_dict,
            message=f"Event created successfully!",
            event_link=event_link,
            requires_confirmation=False
        )
        
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")

@app.post("/confirm_bulk_events", response_model=EventResponse)
async def confirm_bulk_events(events: List[ParsedEvent], user_id: str = Query(None)):
    """
    Create multiple confirmed events in Google or Microsoft Calendar.
    """
    _require_session(user_id)
    try:
        logger.info(f"Confirming {len(events)} bulk events")
        
        created_count = 0
        failed_count = 0
        failed_events = []
        
        for event in events:
            try:
                provider = _normalize_provider(getattr(event, "calendar_provider", None))
                service = _calendar_service_for(provider)
                await service.create_calendar_event(
                    event,
                    user_id=user_id,
                    original_text=getattr(event, "original_text", None),
                    calendar_id=getattr(event, "calendar_id", None)
                )
                created_count += 1
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to create event '{event.title}': {error_msg}")
                failed_count += 1
                failed_events.append({
                    "title": event.title,
                    "error": error_msg
                })
        
        # Build detailed message
        if created_count == 0 and failed_count > 0:
            # All events failed - check if it's a permission error
            if any("write access" in event.get("error", "").lower() or "requiredAccessLevel" in event.get("error", "") for event in failed_events):
                message = f"All events failed: You don't have write access to the selected calendar. Please select a calendar where you have writer or owner permissions."
            else:
                message = f"Failed to create {failed_count} event(s). Please check the error messages and try again."
        elif failed_count > 0:
            message = f"Successfully created {created_count} event(s), but {failed_count} event(s) failed. "
            if any("write access" in event.get("error", "").lower() for event in failed_events):
                message += "Some events failed due to calendar permissions. Please select a writable calendar."
            else:
                message += "Please check the error messages and try again."
        else:
            message = f"Successfully created {created_count} event(s)!"
        
        return EventResponse(
            success=created_count > 0,
            message=message,
            requires_confirmation=False
        )
        
    except Exception as e:
        logger.error(f"Error creating bulk events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create bulk events: {str(e)}")

async def _start_sign_in(provider: str, service, redirect_uri: Optional[str], user_id: Optional[str]):
    if not token_store.is_allowed_redirect_uri(redirect_uri):
        raise HTTPException(
            status_code=400,
            detail="Sign-in must be started from the Prompt2Cal extension. Please update the extension.",
        )
    state = token_store.create_pending_state(provider, redirect_uri, previous_session=user_id)
    try:
        auth_url = await service.get_auth_url(state)
    except Exception as e:
        logger.error(f"Error getting {provider} auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get auth URL: {str(e)}")
    return {"auth_url": auth_url, "provider": provider}

@app.get("/auth/google")
async def google_auth(redirect_uri: str = None, user_id: str = None):
    """
    Initiate Google OAuth2 authentication flow.

    ``redirect_uri`` is the extension's chrome.identity redirect URL, which
    receives the new session when sign-in completes. ``user_id`` is the
    caller's current session, whose other calendar connections carry over.
    """
    return await _start_sign_in("google", calendar_service, redirect_uri, user_id)

@app.get("/auth/microsoft")
async def microsoft_auth(redirect_uri: str = None, user_id: str = None):
    """Initiate Microsoft OAuth2 authentication flow for Outlook calendar."""
    return await _start_sign_in("microsoft", microsoft_calendar_service, redirect_uri, user_id)

@app.post("/auth/logout")
async def logout(user_id: str = None, provider: str = None):
    """
    Logout and clear user credentials for one or both calendar providers.
    """
    _require_session(user_id)
    try:
        if provider is None:
            google_ok = calendar_service.logout(user_id=user_id)
            microsoft_ok = microsoft_calendar_service.logout(user_id=user_id)
            success = google_ok or microsoft_ok
        elif _normalize_provider(provider) == "microsoft":
            success = microsoft_calendar_service.logout(user_id=user_id)
        else:
            success = calendar_service.logout(user_id=user_id)
        return {
            "success": success,
            "message": "Successfully logged out" if success else "No token to remove"
        }
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to logout: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Prompt2Cal API is running"}

SIGN_IN_LINK_INVALID_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Sign-in Failed</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }
        .error { background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px;
                 border: 1px solid #f5c6cb; margin: 20px auto; max-width: 400px; }
    </style>
</head>
<body>
    <div class="error">
        <h2>Sign-in link expired or invalid</h2>
        <p>Please connect your calendar again from the Prompt2Cal extension.</p>
    </div>
</body>
</html>
"""


async def _finish_sign_in(provider: str, service, code: Optional[str], state: Optional[str], error: Optional[str]):
    """Complete an OAuth callback and hand a new session to the extension that started it.

    The session goes only to the chrome.identity redirect URL recorded when the
    sign-in started, so a sign-in link forwarded to someone else never gives
    the sender access to that person's calendar.
    """
    pending = token_store.consume_pending_state(state, provider)
    if not pending:
        return HTMLResponse(content=SIGN_IN_LINK_INVALID_HTML, status_code=400)

    redirect_uri = pending["redirect_uri"]
    if error or not code:
        return RedirectResponse(f"{redirect_uri}#error=access_denied", status_code=302)
    try:
        token_data = await service.exchange_code(code)
    except Exception as e:
        logger.error(f"Error handling {provider} auth callback: {str(e)}")
        return RedirectResponse(f"{redirect_uri}#error=sign_in_failed", status_code=302)

    session = token_store.start_session(pending["previous_session"])
    service.save_token(session, token_data)
    return RedirectResponse(f"{redirect_uri}#session={session}", status_code=302)

@app.get("/auth/callback")
async def google_auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle Google OAuth2 callback and store credentials."""
    return await _finish_sign_in("google", calendar_service, code, state, error)

@app.get("/auth/microsoft/callback")
async def microsoft_auth_callback(code: str = None, state: str = None, error: str = None):
    """Handle Microsoft OAuth2 callback and store credentials."""
    return await _finish_sign_in("microsoft", microsoft_calendar_service, code, state, error)

@app.post("/find_meeting_slots")
async def find_meeting_slots(request: dict):
    """
    Find available meeting slots in a given time range.
    """
    user_id = request.get("user_id")
    _require_session(user_id)
    try:
        # Parse request parameters
        duration_minutes = request.get("duration_minutes", 60)
        start_date_str = request.get("start_date")
        end_date_str = request.get("end_date")
        working_hours = request.get("working_hours", [9, 17])
        buffer_minutes = request.get("buffer_minutes", 15)
        
        if not start_date_str or not end_date_str:
            raise HTTPException(status_code=400, detail="start_date and end_date are required")
        
        # Parse dates
        from datetime import datetime
        start_date = datetime.fromisoformat(start_date_str)
        end_date = datetime.fromisoformat(end_date_str)
        
        # Find available slots
        available_slots = await calendar_service.find_available_slots(
            duration_minutes=duration_minutes,
            start_date=start_date,
            end_date=end_date,
            working_hours=tuple(working_hours),
            buffer_minutes=buffer_minutes,
            user_id=user_id
        )
        
        return {
            "success": True,
            "available_slots": available_slots,
            "total_slots": len(available_slots),
            "message": f"Found {len(available_slots)} available slots"
        }
        
    except Exception as e:
        logger.error(f"Error finding meeting slots: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to find meeting slots: {str(e)}")

@app.post("/check_conflicts")
async def check_conflicts(request: dict):
    """
    Check if a proposed meeting time conflicts with existing events.
    """
    user_id = request.get("user_id")
    _require_session(user_id)
    try:
        # Parse request parameters
        start_time_str = request.get("start_time")
        end_time_str = request.get("end_time")
        buffer_minutes = request.get("buffer_minutes", 15)
        calendar_id = request.get("calendar_id")
        duration_minutes = request.get("duration_minutes", 60)
        recurrence_type = request.get("recurrence_type")
        recurrence_count = request.get("recurrence_count")
        recurrence_interval = request.get("recurrence_interval", 1)
        end_date = request.get("end_date")
        provider = _normalize_provider(request.get("calendar_provider") or request.get("provider"))
        
        if not start_time_str or not end_time_str:
            raise HTTPException(status_code=400, detail="start_time and end_time are required")
        
        # Parse times
        from datetime import datetime
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00') if 'Z' in start_time_str else start_time_str)
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00') if 'Z' in end_time_str else end_time_str)
        
        # Calculate duration if not provided
        if not duration_minutes:
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
        
        if provider == "microsoft":
            conflicts = await microsoft_calendar_service.check_conflicts(
                start_time=start_time_str,
                end_time=end_time_str,
                user_id=user_id,
                calendar_id=calendar_id,
                buffer_minutes=buffer_minutes,
            )
        else:
            # Token refresh is handled inside check_conflicts method
            conflicts = await calendar_service.check_conflicts(
                start_time=start_time,
                end_time=end_time,
                buffer_minutes=buffer_minutes,
                calendar_id=calendar_id,
                recurrence_type=recurrence_type,
                recurrence_count=recurrence_count,
                recurrence_interval=recurrence_interval,
                end_date=end_date,
                user_id=user_id
            )
        
        return {
            "success": True,
            "conflicts": conflicts,
            "has_conflicts": len(conflicts) > 0,
            "message": f"Found {len(conflicts)} conflict(s)" if conflicts else "No conflicts found"
        }
        
    except Exception as e:
        logger.error(f"Error checking conflicts: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to check conflicts: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
