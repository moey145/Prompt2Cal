from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class RecurrenceType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class EventRequest(BaseModel):
    text: str = Field(..., description="Natural language description of the event")
    timezone: Optional[str] = Field(None, description="Client IANA timezone, e.g., 'America/New_York'")
    user_id: Optional[str] = Field(None, description="User ID for authentication")
    force_multiple: Optional[bool] = Field(False, description="Force parsing as multiple events")

class ParsedEvent(BaseModel):
    title: str = Field(..., description="Event title")
    start_time: str = Field(..., description="Start time in ISO 8601 format")
    end_time: Optional[str] = Field(None, description="End time in ISO 8601 format")
    location: Optional[str] = Field(None, description="Event location")
    notes: Optional[str] = Field(None, description="Additional notes")
    duration_minutes: Optional[int] = Field(60, description="Event duration in minutes")
    recurrence_type: RecurrenceType = Field(RecurrenceType.NONE, description="Recurrence pattern")
    recurrence_count: Optional[int] = Field(None, description="Number of occurrences")
    recurrence_interval: Optional[int] = Field(1, description="Interval between recurrences")
    color: Optional[str] = Field("#4285f4", description="Event color in hex format")
    reminder: Optional[str] = Field("none", description="Reminder time in minutes before event (or 'none')")
    buffer_before: Optional[int] = Field(0, description="Buffer time in minutes before the event")
    buffer_after: Optional[int] = Field(0, description="Buffer time in minutes after the event")
    end_date: Optional[str] = Field(None, description="End date for recurring events (ISO format)")
    end_after_count: Optional[int] = Field(None, description="End after N occurrences")
    original_text: Optional[str] = Field(None, description="Original natural language input that produced this event")

class BulkEventRequest(BaseModel):
    text: str = Field(..., description="Natural language description for bulk events")
    count: Optional[int] = Field(None, description="Number of events to create")
    start_date: Optional[str] = Field(None, description="Start date for bulk events")

class BulkEventResponse(BaseModel):
    success: bool
    parsed_events: List[Dict[str, Any]] = Field(default_factory=list)
    message: str
    total_created: Optional[int] = None

class FileImportRequest(BaseModel):
    file_content: str = Field(..., description="Content of uploaded file")
    file_type: str = Field(..., description="Type of file (csv, txt)")

class EventResponse(BaseModel):
    model_config = {"from_attributes": True, "arbitrary_types_allowed": True}
    
    success: bool
    parsed_event: Optional[Dict[str, Any]] = None
    parsed_events: Optional[List[Dict[str, Any]]] = None
    message: str
    event_link: Optional[str] = None
    requires_confirmation: bool = False
    is_bulk: bool = False
