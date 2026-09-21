"""Tests for server-issued sessions, OAuth sign-in state and per-user calendar access."""

import asyncio
import os
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.services import token_store
from backend.services.calendar_service import CalendarService

EXTENSION_REDIRECT = "https://abcdefghijklmnopabcdefghijklmnop.chromiumapp.org/oauth"


@pytest.fixture(autouse=True)
def token_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TOKEN_STORAGE_DIR", str(tmp_path))
    monkeypatch.delenv("CHROME_EXTENSION_ID", raising=False)
    return tmp_path


@pytest.fixture
def client(monkeypatch):
    for service in (main.calendar_service, main.microsoft_calendar_service):
        monkeypatch.setattr(service, "CLIENT_ID", "test-client-id")
        monkeypatch.setattr(service, "CLIENT_SECRET", "test-client-secret")

    async def google_exchange(code):
        return {"token": f"google-{code}", "refresh_token": "r", "auth_timestamp": "2099-01-01T00:00:00"}

    async def microsoft_exchange(code):
        return {"access_token": f"ms-{code}", "refresh_token": "r"}

    monkeypatch.setattr(main.calendar_service, "exchange_code", google_exchange)
    monkeypatch.setattr(main.microsoft_calendar_service, "exchange_code", microsoft_exchange)
    return TestClient(main.app)


def sign_in(client, provider="google", previous_session=None, code="code"):
    params = {"redirect_uri": EXTENSION_REDIRECT}
    if previous_session:
        params["user_id"] = previous_session
    start = client.get(f"/auth/{provider}", params=params)
    assert start.status_code == 200, start.text
    state = parse_qs(urlsplit(start.json()["auth_url"]).query)["state"][0]
    callback_path = "/auth/callback" if provider == "google" else "/auth/microsoft/callback"
    return state, client.get(callback_path, params={"code": code, "state": state}, follow_redirects=False)


def session_from(response):
    location = response.headers["location"]
    assert location.startswith(EXTENSION_REDIRECT + "#session=")
    return location.split("#session=", 1)[1]


class TestTokenStore:
    @pytest.mark.parametrize(
        "user_id",
        [None, "", "user_ngrj32xjn", "../token", "/tmp/anything", "s_" + "a" * 42, "s_" + "a" * 42 + "/"],
    )
    def test_rejects_anything_the_server_did_not_issue(self, user_id):
        assert not token_store.is_valid_session(user_id)
        with pytest.raises(token_store.InvalidSession):
            token_store.token_path("google", user_id)

    def test_issued_sessions_stay_inside_token_dir(self, token_dir):
        session = token_store.start_session()
        assert token_store.is_valid_session(session)
        assert os.path.dirname(token_store.token_path("microsoft", session)) == str(token_dir)

    @pytest.mark.parametrize(
        "uri",
        [
            None,
            "",
            "http://abcdefghijklmnopabcdefghijklmnop.chromiumapp.org/oauth",
            "https://evil.example/oauth",
            "https://abcdefghijklmnopabcdefghijklmnop.chromiumapp.org.evil.example/",
            "https://user@abcdefghijklmnopabcdefghijklmnop.chromiumapp.org/",
            "https://abcdefghijklmnopabcdefghijklmnop.chromiumapp.org:8443/",
            EXTENSION_REDIRECT + "#x",
        ],
    )
    def test_only_extension_redirects_can_receive_a_session(self, uri):
        assert not token_store.is_allowed_redirect_uri(uri)

    def test_pinned_extension_id(self, monkeypatch):
        assert token_store.is_allowed_redirect_uri(EXTENSION_REDIRECT)
        monkeypatch.setenv("CHROME_EXTENSION_ID", "p" * 32)
        assert not token_store.is_allowed_redirect_uri(EXTENSION_REDIRECT)
        assert token_store.is_allowed_redirect_uri(f"https://{'p' * 32}.chromiumapp.org/oauth")

    def test_pending_state_is_single_use_and_provider_bound(self):
        state = token_store.create_pending_state("google", EXTENSION_REDIRECT)
        assert token_store.consume_pending_state(state, "microsoft") is None
        other = token_store.create_pending_state("google", EXTENSION_REDIRECT)
        assert token_store.consume_pending_state(other, "google")["redirect_uri"] == EXTENSION_REDIRECT
        assert token_store.consume_pending_state(other, "google") is None

    def test_expired_pending_state_is_rejected(self, monkeypatch):
        state = token_store.create_pending_state("google", EXTENSION_REDIRECT)
        monkeypatch.setattr(token_store, "PENDING_STATE_TTL_SECONDS", -1)
        assert token_store.consume_pending_state(state, "google") is None


class TestPerRequestCalendarClient:
    @pytest.mark.parametrize("user_id", ["valid-but-unknown", None, "../token"])
    def test_never_falls_back_to_another_users_calendar(self, user_id):
        if user_id == "valid-but-unknown":
            user_id = token_store.start_session()
        service = CalendarService()
        with pytest.raises(Exception):
            asyncio.run(service.get_calendars(user_id=user_id))
        assert not hasattr(service, "service")


class TestApiSessions:
    @pytest.mark.parametrize(
        "method, path, kwargs",
        [
            ("get", "/calendars", {}),
            ("get", "/calendars", {"params": {"user_id": "../token"}}),
            ("post", "/confirm_event", {"params": {"user_id": "user_ngrj32xjn"},
                                        "json": {"title": "x", "start_time": "2026-01-01T10:00:00"}}),
            ("post", "/confirm_bulk_events", {"json": []}),
            ("post", "/check_conflicts", {"json": {"user_id": "/tmp/x"}}),
            ("post", "/find_meeting_slots", {"json": {}}),
            ("post", "/auth/logout", {"params": {"user_id": "../credentials"}}),
        ],
    )
    def test_calendar_endpoints_need_an_issued_session(self, client, method, path, kwargs):
        assert getattr(client, method)(path, **kwargs).status_code == 401

    @pytest.mark.parametrize(
        "params",
        [{"user_id": "user_ngrj32xjn"}, {"redirect_uri": "https://evil.example/oauth"}],
    )
    def test_sign_in_must_come_from_the_extension(self, client, params):
        assert client.get("/auth/google", params=params).status_code == 400

    def test_sign_in_hands_a_new_session_to_the_extension_once(self, client):
        state, callback = sign_in(client)
        assert callback.status_code == 302
        session = session_from(callback)
        assert token_store.is_valid_session(session)
        status = client.get("/auth/status", params={"user_id": session}).json()
        assert status["providers"] == {"google": True, "microsoft": False}

        replay = client.get("/auth/callback", params={"code": "again", "state": state}, follow_redirects=False)
        assert replay.status_code == 400
        assert "location" not in replay.headers

    @pytest.mark.parametrize("state", ["user_ngrj32xjn", "A" * 43, None])
    def test_callback_rejects_states_it_did_not_issue(self, client, state):
        params = {"code": "code"} if state is None else {"code": "code", "state": state}
        response = client.get("/auth/callback", params=params, follow_redirects=False)
        assert response.status_code == 400
        assert "location" not in response.headers

    def test_declined_consent_reports_an_error_to_the_extension(self, client):
        start = client.get("/auth/google", params={"redirect_uri": EXTENSION_REDIRECT})
        state = parse_qs(urlsplit(start.json()["auth_url"]).query)["state"][0]
        response = client.get(
            "/auth/callback", params={"error": "access_denied", "state": state}, follow_redirects=False
        )
        assert response.headers["location"] == EXTENSION_REDIRECT + "#error=access_denied"

    def test_connecting_outlook_keeps_google_connected(self, client):
        _, google_callback = sign_in(client, "google")
        first = session_from(google_callback)
        _, microsoft_callback = sign_in(client, "microsoft", previous_session=first)
        second = session_from(microsoft_callback)

        assert second != first
        providers = lambda s: client.get("/auth/status", params={"user_id": s}).json()["providers"]
        assert providers(second) == {"google": True, "microsoft": True}
        assert providers(first) == {"google": False, "microsoft": False}
