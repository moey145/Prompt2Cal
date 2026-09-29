"""Tests for the slot, alternative and category endpoints, for both providers."""

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.services import token_store


@pytest.fixture(autouse=True)
def token_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_STORAGE_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def session():
    return token_store.start_session()


@pytest.fixture
def client():
    return TestClient(main.app)


def google_events(*windows):
    """Google's shape: nested dicts, and all-day entries carry only a date."""
    return [
        {"summary": "Busy", "start": {"dateTime": start}, "end": {"dateTime": end}}
        for start, end in windows
    ]


def outlook_events(*windows):
    """The Outlook service's shape: plain ISO strings."""
    return [{"summary": "Busy", "start": start, "end": end} for start, end in windows]


def stub_events(monkeypatch, provider, events):
    service = main.microsoft_calendar_service if provider == "microsoft" else main.calendar_service

    async def fake_get_events_in_range(start_time, end_time, user_id=None, calendar_id=None, **kwargs):
        return events

    monkeypatch.setattr(service, "get_events_in_range", fake_get_events_in_range)


class TestSuggestAlternatives:
    @pytest.mark.parametrize("provider", ["google", "microsoft"])
    def test_offers_a_slot_before_and_after_the_clash(self, client, monkeypatch, session, provider):
        busy = ("2026-10-01T14:00:00+10:00", "2026-10-01T15:00:00+10:00")
        events = google_events(busy) if provider == "google" else outlook_events(busy)
        stub_events(monkeypatch, provider, events)

        response = client.post(
            "/suggest_alternatives",
            json={
                "user_id": session,
                "calendar_provider": provider,
                "start_time": "2026-10-01T14:00:00+10:00",
                "end_time": "2026-10-01T15:00:00+10:00",
            },
        )
        assert response.status_code == 200
        alternatives = response.json()["alternatives"]
        assert [a["start"] for a in alternatives] == [
            "2026-10-01T13:00:00+10:00",
            "2026-10-01T15:00:00+10:00",
        ]
        assert alternatives[0]["minutes_from_proposed"] == -60

    def test_all_day_entries_do_not_block_the_day(self, client, monkeypatch, session):
        monkeypatch.setattr(
            main.calendar_service,
            "get_events_in_range",
            _const([{"summary": "Holiday", "start": {"date": "2026-10-01"}, "end": {"date": "2026-10-02"}}]),
        )
        response = client.post(
            "/suggest_alternatives",
            json={
                "user_id": session,
                "start_time": "2026-10-01T14:00:00+10:00",
                "end_time": "2026-10-01T15:00:00+10:00",
            },
        )
        assert len(response.json()["alternatives"]) == 2

    def test_a_full_day_leaves_nothing_to_suggest(self, client, monkeypatch, session):
        stub_events(
            monkeypatch,
            "google",
            google_events(("2026-10-01T08:00:00+10:00", "2026-10-01T20:00:00+10:00")),
        )
        response = client.post(
            "/suggest_alternatives",
            json={
                "user_id": session,
                "start_time": "2026-10-01T14:00:00+10:00",
                "end_time": "2026-10-01T15:00:00+10:00",
            },
        )
        assert response.json()["alternatives"] == []

    def test_needs_a_session_and_times(self, client, session):
        assert client.post("/suggest_alternatives", json={}).status_code == 401
        assert client.post("/suggest_alternatives", json={"user_id": session}).status_code == 400


class TestFindMeetingSlots:
    @pytest.mark.parametrize("provider", ["google", "microsoft"])
    def test_finds_gaps_within_working_hours(self, client, monkeypatch, session, provider):
        busy = ("2026-10-01T09:00:00+10:00", "2026-10-01T12:00:00+10:00")
        events = google_events(busy) if provider == "google" else outlook_events(busy)
        stub_events(monkeypatch, provider, events)

        response = client.post(
            "/find_meeting_slots",
            json={
                "user_id": session,
                "calendar_provider": provider,
                "start_date": "2026-10-01T08:00:00+10:00",
                "end_date": "2026-10-01T18:00:00+10:00",
                "duration_minutes": 60,
                "working_hours": [9, 17],
                "buffer_minutes": 0,
            },
        )
        assert response.status_code == 200
        slots = response.json()["available_slots"]
        assert slots, "expected free slots in the afternoon"
        assert all(slot["duration_minutes"] == 60 for slot in slots)
        assert slots[0]["start"] == "2026-10-01T12:00:00+10:00"

    def test_working_hours_follow_the_users_timezone(self, client, monkeypatch, session):
        # The browser sends UTC; 9am in Sydney is 23:00 UTC the day before.
        stub_events(monkeypatch, "google", [])
        response = client.post(
            "/find_meeting_slots",
            json={
                "user_id": session,
                "calendar_provider": "google",
                "start_date": "2026-09-30T20:00:00Z",
                "end_date": "2026-10-01T14:00:00Z",
                "timezone": "Australia/Sydney",
                "duration_minutes": 60,
            },
        )
        slots = response.json()["available_slots"]
        assert slots[0]["start"] == "2026-10-01T09:00:00+10:00"
        assert slots[-1]["end"] <= "2026-10-01T17:00:00+10:00"

    def test_several_days_each_get_slots(self, client, monkeypatch, session):
        stub_events(monkeypatch, "google", [])
        response = client.post(
            "/find_meeting_slots",
            json={
                "user_id": session,
                "calendar_provider": "google",
                "start_date": "2026-10-01T09:00:00+10:00",
                "end_date": "2026-10-03T00:00:00+10:00",
                "duration_minutes": 30,
            },
        )
        days = {slot["start"][:10] for slot in response.json()["available_slots"]}
        assert days == {"2026-10-01", "2026-10-02"}


class TestCategories:
    def test_google_has_none(self, client, session):
        response = client.get("/calendar_categories", params={"user_id": session, "provider": "google"})
        assert response.json() == {"success": True, "provider": "google", "categories": []}

    def test_outlook_returns_the_mailbox_categories(self, client, monkeypatch, session):
        async def fake_categories(user_id=None):
            return [{"name": "Red category", "color": "preset0"}]

        monkeypatch.setattr(main.microsoft_calendar_service, "get_categories", fake_categories)
        response = client.get(
            "/calendar_categories", params={"user_id": session, "provider": "microsoft"}
        )
        assert response.json()["categories"] == [{"name": "Red category", "color": "preset0"}]

    def test_needs_a_session(self, client):
        assert client.get("/calendar_categories").status_code == 401


SLOT_REQUEST = {
    "start_date": "2026-10-01T09:00:00+10:00",
    "end_date": "2026-10-02T17:00:00+10:00",
    "duration_minutes": 60,
}


class TestCalendarReadErrors:
    @pytest.mark.parametrize(
        "provider, name", [("google", "Google"), ("microsoft", "Outlook")]
    )
    def test_unconnected_calendar_gets_one_short_message(self, client, session, provider, name):
        # A signed-in session with no token for this provider.
        response = client.post(
            "/find_meeting_slots",
            json={"user_id": session, "calendar_provider": provider, **SLOT_REQUEST},
        )
        assert response.status_code == 409
        assert response.json()["detail"] == (
            f"Connect {name} Calendar in Settings to find free slots."
        )

    def test_other_failures_hide_the_technical_detail(self, client, monkeypatch, session):
        async def broken(*args, **kwargs):
            raise Exception("Failed to get calendar events: <HttpError 500 ...>")

        monkeypatch.setattr(main.calendar_service, "get_events_in_range", broken)
        response = client.post(
            "/find_meeting_slots",
            json={"user_id": session, "calendar_provider": "google", **SLOT_REQUEST},
        )
        assert response.status_code == 502
        assert response.json()["detail"] == "Couldn't read your calendar. Try again in a moment."

    def test_health_lists_the_providers_the_slot_finder_supports(self, client):
        assert client.get("/health").json()["slot_finder_providers"] == ["google", "microsoft"]


def _const(value):
    async def fake(*args, **kwargs):
        return value

    return fake
