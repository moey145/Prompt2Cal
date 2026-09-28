"""Tests for the Outlook event body, where the options differ from Google's."""

import pytest

from backend.models.event_models import ParsedEvent
from backend.services.microsoft_calendar_service import MicrosoftCalendarService


@pytest.fixture
def service():
    return MicrosoftCalendarService()


def make_event(**overrides):
    event = {
        "title": "Team sync",
        "start_time": "2026-10-01T10:00:00+10:00",
        "end_time": "2026-10-01T11:00:00+10:00",
        "timezone": "Australia/Sydney",
    }
    event.update(overrides)
    return ParsedEvent(**event)


@pytest.mark.parametrize(
    "reminder, expected_on, expected_minutes",
    [
        ("30", True, 30),
        ("0", True, 0),
        ("none", False, None),
        (None, False, None),
        ("not-a-number", False, None),
    ],
)
def test_reminder_maps_to_graph_lead_time(service, reminder, expected_on, expected_minutes):
    body = service._build_event_body(make_event(reminder=reminder))
    assert body["isReminderOn"] is expected_on
    assert body.get("reminderMinutesBeforeStart") == expected_minutes


def test_conference_request_creates_a_teams_meeting(service):
    body = service._build_event_body(make_event(add_conference=True))
    assert body["isOnlineMeeting"] is True
    assert body["onlineMeetingProvider"] == "teamsForBusiness"


def test_colour_is_not_sent_to_graph(service):
    # Graph has no per-event colour, only named categories, so the hex colour
    # the Google UI collects must not leak into the request.
    body = service._build_event_body(make_event(color="#d50000"))
    assert "color" not in body
    assert "#d50000" not in str(body)
