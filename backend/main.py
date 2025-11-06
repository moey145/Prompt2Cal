from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
import logging

from backend.services.event_parser import EventParser
from backend.services.calendar_service import CalendarService
from backend.models.event_models import (
    EventRequest, EventResponse, ParsedEvent,
    BulkEventRequest, BulkEventResponse, FileImportRequest
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Prompt2Cal API",
    description="Convert natural language to calendar events",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
event_parser = EventParser()
calendar_service = CalendarService()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/auth/status")
async def auth_status(user_id: str = None):
    """Check if Google Calendar is authenticated."""
    try:
        is_authenticated = calendar_service.is_authenticated(user_id=user_id)
        return {
            "authenticated": is_authenticated,
            "message": "Authenticated" if is_authenticated else "Not authenticated"
        }
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        return {"authenticated": False, "message": f"Error: {str(e)}"}

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
                        events_list.append(event.model_dump())
                    elif isinstance(event, dict):
                        events_list.append(event)
                    else:
                        events_list.append(event.dict() if hasattr(event, 'dict') else event.model_dump())
                
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
                # Check if the single event is recurring and needs expansion
                single_event = parsed_events[0]
                recurrence_str = (
                    single_event.recurrence_type.value
                    if hasattr(single_event, 'recurrence_type') and hasattr(single_event.recurrence_type, 'value')
                    else str(getattr(single_event, 'recurrence_type', '') or '').lower()
                )
                recurrence_count = getattr(single_event, 'recurrence_count', None)
                end_date = getattr(single_event, 'end_date', None)
                # Expand ONLY if: (recurrence_count is explicitly set and > 1) OR (end_date is set)
                # Do NOT expand indefinite recurring events (no count, no end_date)
                # CRITICAL: If recurrence_count is None, it's indefinite - do NOT expand
                should_expand = (
                    recurrence_str and 
                    recurrence_str != "none" and 
                    recurrence_count is not None and  # Must have explicit count
                    recurrence_count > 1 and  # Must be > 1
                    end_date is None  # If end_date is set, expand separately
                ) or (
                    recurrence_str and 
                    recurrence_str != "none" and 
                    end_date is not None  # Expand if end_date is explicitly set
                )
                if should_expand:
                    logger.info(
                        f"Single recurring event detected, expanding: type={recurrence_str}, count={recurrence_count}, end_date={end_date}"
                    )
                    try:
                        expanded = await event_parser.event_expander.expand_single_recurring_event(single_event, tz_name=request.timezone, original_input=request.text)
                        if expanded and len(expanded) > 1:
                            events_list = [
                                e.model_dump() if hasattr(e, 'model_dump') else (e.dict() if hasattr(e, 'dict') else e)
                                for e in expanded
                            ]
                            return JSONResponse(content={
                                "success": True,
                                "parsed_event": None,
                                "parsed_events": events_list,
                                "message": "",
                                "event_link": None,
                                "requires_confirmation": True,
                                "is_bulk": True
                            })
                    except Exception as ex:
                        logger.warning(f"Failed to expand single recurring event: {ex}")
                elif recurrence_str and recurrence_str != "none" and recurrence_count is None and end_date is None:
                    # Indefinite recurring event - log it but don't expand
                    logger.info(
                        f"Indefinite recurring event detected in multiple path, NOT expanding: type={recurrence_str}, count=None (indefinite)"
                    )

                # Try text-based expansion as a fallback when only 1 event came back
                try:
                    alt_expanded = await event_parser.expand_recurring_events(request.text, request.timezone)
                    if alt_expanded and len(alt_expanded) > 1:
                        events_list = [
                            e.model_dump() if hasattr(e, 'model_dump') else (e.dict() if hasattr(e, 'dict') else e)
                            for e in alt_expanded
                        ]
                        return JSONResponse(content={
                            "success": True,
                            "parsed_event": None,
                            "parsed_events": events_list,
                            "message": "",
                            "event_link": None,
                            "requires_confirmation": True,
                            "is_bulk": True
                        })
                except Exception as ex:
                    logger.warning(f"Alternate recurring expansion in multi failed: {ex}")
                
                logger.info("Multiple events detected but only 1 event returned, falling back to single event")
        
        # Parse single event (with timezone passed in)
        parsed_event = await event_parser.parse_event_text(request.text, tz_name=request.timezone)

        # If user clicked Single Event button (force_multiple=False), NEVER expand
        # Always return exactly 1 event
        if request.force_multiple is False:
            logger.info("Single Event button clicked - returning exactly 1 event (no expansion)")
            # Strip recurrence info if present to ensure it's a single event
            if hasattr(parsed_event, 'recurrence_type'):
                parsed_event.recurrence_type = "none"
            if hasattr(parsed_event, 'recurrence_count'):
                parsed_event.recurrence_count = None
            if hasattr(parsed_event, 'recurrence_interval'):
                parsed_event.recurrence_interval = 1
            if hasattr(parsed_event, 'end_date'):
                parsed_event.end_date = None
        else:
            # For auto-detect (None) or Multiple Events button (True), expand recurring events
            # Only expand if there's an explicit count > 1 or an end_date (not for indefinite events)
            recurrence_str = (
                parsed_event.recurrence_type.value
                if hasattr(parsed_event, 'recurrence_type') and hasattr(parsed_event.recurrence_type, 'value')
                else str(getattr(parsed_event, 'recurrence_type', '') or '').lower()
            )
            recurrence_count = getattr(parsed_event, 'recurrence_count', None)
            end_date = getattr(parsed_event, 'end_date', None)
            # Expand ONLY if: (recurrence_count is explicitly set and > 1) OR (end_date is set)
            # Do NOT expand indefinite recurring events (no count, no end_date)
            # CRITICAL: If recurrence_count is None, it's indefinite - do NOT expand
            should_expand = (
                recurrence_str and 
                recurrence_str != "none" and 
                recurrence_count is not None and  # Must have explicit count
                recurrence_count > 1 and  # Must be > 1
                end_date is None  # If end_date is set, expand separately
            ) or (
                recurrence_str and 
                recurrence_str != "none" and 
                end_date is not None  # Expand if end_date is explicitly set
            )
            if should_expand:
                logger.info(
                    f"Single parse yielded recurring event, expanding for UI preview: type={recurrence_str}, count={recurrence_count}, end_date={end_date}"
                )
                try:
                    expanded = await event_parser.event_expander.expand_single_recurring_event(parsed_event, tz_name=request.timezone, original_input=request.text)
                    if expanded and len(expanded) > 1:
                        events_list = [
                            e.model_dump() if hasattr(e, 'model_dump') else (e.dict() if hasattr(e, 'dict') else e)
                            for e in expanded
                        ]
                        return JSONResponse(content={
                            "success": True,
                            "parsed_event": None,
                            "parsed_events": events_list,
                            "message": "",
                            "event_link": None,
                            "requires_confirmation": True,
                            "is_bulk": True
                        })
                except Exception as ex:
                    logger.warning(f"Failed to expand recurring event for preview: {ex}")
            elif recurrence_str and recurrence_str != "none" and recurrence_count is None and end_date is None:
                # Indefinite recurring event - log it but don't expand
                logger.info(
                    f"Indefinite recurring event detected, NOT expanding for UI preview: type={recurrence_str}, count=None (indefinite)"
                )

        # As a final fallback: if UI asked for multiple and we still have one, try text-based expansion
        # Only do this if Multiple Events button was clicked
        if is_multiple and request.force_multiple:
            try:
                alt_expanded = await event_parser.expand_recurring_events(request.text, request.timezone)
                if alt_expanded and len(alt_expanded) > 1:
                    events_list = [
                        e.model_dump() if hasattr(e, 'model_dump') else (e.dict() if hasattr(e, 'dict') else e)
                        for e in alt_expanded
                    ]
                    return JSONResponse(content={
                        "success": True,
                        "parsed_event": None,
                        "parsed_events": events_list,
                        "message": "",
                        "event_link": None,
                        "requires_confirmation": True,
                        "is_bulk": True
                    })
            except Exception as ex:
                logger.warning(f"Alternate recurring expansion failed: {ex}")

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
    Confirm and create the calendar event.
    
    Process:
    1. Validate the parsed event data
    2. Create event in Google Calendar
    3. Return success with event link
    """
    try:
        logger.info(f"Confirming event: {parsed_event.title}")
        
        # Step 4: Create event in Google Calendar
        event_link = await calendar_service.create_calendar_event(parsed_event, user_id=user_id)
        
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

@app.post("/create_bulk_events", response_model=BulkEventResponse)
async def create_bulk_events(request: BulkEventRequest):
    """
    Create multiple events from natural language bulk requests.
    
    Examples:
    - "Create 5 meetings every day this week at 2pm"
    - "Create 3 appointments every week for the next month"
    """
    try:
        logger.info(f"Processing bulk event request: {request.text}")
        
        # Parse bulk events
        parsed_events = await event_parser.parse_bulk_events(
            request.text, 
            request.count, 
            request.start_date
        )
        
        if not parsed_events:
            raise HTTPException(status_code=400, detail="No events could be parsed from the request")
        
        # Convert to dicts
        events_list = [
            event.model_dump() if isinstance(event, ParsedEvent) else event
            for event in parsed_events
        ]
        
        return BulkEventResponse(
            success=True,
            parsed_events=events_list,
            message=f"Successfully parsed {len(parsed_events)} events for bulk creation.",
            total_created=len(parsed_events)
        )
        
    except Exception as e:
        logger.error(f"Error parsing bulk events: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse bulk events: {str(e)}")

@app.post("/import_events", response_model=BulkEventResponse)
async def import_events(request: FileImportRequest):
    """
    Import events from CSV or text files.
    
    CSV format: Title,Start Time,End Time,Location,Notes
    Text format: One event description per line
    """
    try:
        logger.info(f"Processing file import: {request.file_type}")
        
        # Parse events from file content
        parsed_events = await event_parser.parse_file_import(
            request.file_content, 
            request.file_type
        )
        
        if not parsed_events:
            raise HTTPException(status_code=400, detail="No events could be parsed from the file")
        
        return BulkEventResponse(
            success=True,
            parsed_events=parsed_events,
            message=f"Successfully imported {len(parsed_events)} events from file.",
            total_created=len(parsed_events)
        )
        
    except Exception as e:
        logger.error(f"Error importing events: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to import events: {str(e)}")

@app.post("/confirm_bulk_events", response_model=EventResponse)
async def confirm_bulk_events(events: List[ParsedEvent], user_id: str = Query(None)):
    """
    Create multiple confirmed events in Google Calendar.
    """
    try:
        logger.info(f"Confirming {len(events)} bulk events")
        
        created_count = 0
        failed_count = 0
        
        for event in events:
            try:
                await calendar_service.create_calendar_event(event, user_id=user_id)
                created_count += 1
            except Exception as e:
                logger.error(f"Failed to create event '{event.title}': {str(e)}")
                failed_count += 1
        
        message = f"Successfully created {created_count} events"
        if failed_count > 0:
            message += f", {failed_count} failed"
        
        return EventResponse(
            success=created_count > 0,
            message=message,
            requires_confirmation=False
        )
        
    except Exception as e:
        logger.error(f"Error creating bulk events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create bulk events: {str(e)}")

@app.get("/auth/google")
async def google_auth(user_id: str = None):
    """
    Initiate Google OAuth2 authentication flow.
    """
    try:
        auth_url = await calendar_service.get_auth_url(user_id=user_id)
        return {"auth_url": auth_url}
    except Exception as e:
        logger.error(f"Error getting auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get auth URL: {str(e)}")

@app.post("/auth/logout")
async def logout(user_id: str = None):
    """
    Logout and clear user credentials.
    """
    try:
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

@app.get("/auth/callback")
async def google_auth_callback(code: str = None, state: str = None):
    """
    Handle Google OAuth2 callback and store credentials.
    For Chrome extension, return a success page instead of redirecting.
    """
    try:
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not provided")
        
        # Extract user_id from state parameter
        user_id = state if state else None
        
        await calendar_service.handle_auth_callback(code, user_id=user_id)
        
        # Return success page for Chrome extension
        from fastapi.responses import HTMLResponse
        success_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #f5f5f5;
                }
                .success {
                    background-color: #d4edda;
                    color: #155724;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #c3e6cb;
                    margin: 20px auto;
                    max-width: 400px;
                }
                .icon {
                    font-size: 48px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="success">
                <div class="icon">✅</div>
                <h2>Google Calendar Connected!</h2>
                <p>You can now close this tab and return to the Prompt2Cal extension.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=success_html, status_code=200)
        
    except Exception as e:
        logger.error(f"Error handling auth callback: {str(e)}")
        # Return error page for Chrome extension
        from fastapi.responses import HTMLResponse
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Failed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background-color: #f5f5f5;
                }}
                .error {{
                    background-color: #f8d7da;
                    color: #721c24;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid #f5c6cb;
                    margin: 20px auto;
                    max-width: 400px;
                }}
                .icon {{
                    font-size: 48px;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="error">
                <div class="icon">❌</div>
                <h2>Authentication Failed</h2>
                <p>Error: {str(e)}</p>
                <p>Please try again from the Prompt2Cal extension.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=400)

@app.post("/find_meeting_slots")
async def find_meeting_slots(request: dict):
    """
    Find available meeting slots in a given time range.
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Get calendar service for user
        calendar_service = CalendarService()
        await calendar_service.initialize_user_service(user_id)
        
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
            buffer_minutes=buffer_minutes
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
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Get calendar service for user
        calendar_service = CalendarService()
        await calendar_service.initialize_user_service(user_id)
        
        # Parse request parameters
        start_time_str = request.get("start_time")
        end_time_str = request.get("end_time")
        buffer_minutes = request.get("buffer_minutes", 15)
        
        if not start_time_str or not end_time_str:
            raise HTTPException(status_code=400, detail="start_time and end_time are required")
        
        # Parse times
        from datetime import datetime
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
        
        # Check for conflicts
        conflicts = await calendar_service.check_conflicts(
            start_time=start_time,
            end_time=end_time,
            buffer_minutes=buffer_minutes
        )
        
        return {
            "success": True,
            "conflicts": conflicts,
            "has_conflicts": len(conflicts) > 0,
            "message": f"Found {len(conflicts)} conflicts" if conflicts else "No conflicts found"
        }
        
    except Exception as e:
        logger.error(f"Error checking conflicts: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to check conflicts: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
