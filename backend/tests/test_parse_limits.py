"""Tests for the limits protecting the public, LLM-backed parse endpoint."""

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.models.event_models import MAX_EVENT_TEXT_CHARS, ParsedEvent
from backend.services.rate_limit import DailyCounter, SlidingWindowRateLimiter, client_ip


class TestSlidingWindow:
    def test_allows_up_to_the_limit_then_asks_for_a_wait(self):
        limiter = SlidingWindowRateLimiter(limit=3, window_seconds=60)
        assert [limiter.hit("1.2.3.4", now=t) for t in (0, 1, 2)] == [None, None, None]
        assert limiter.hit("1.2.3.4", now=3) is not None

    def test_window_slides(self):
        limiter = SlidingWindowRateLimiter(limit=2, window_seconds=60)
        limiter.hit("1.2.3.4", now=0)
        limiter.hit("1.2.3.4", now=1)
        assert limiter.hit("1.2.3.4", now=30) is not None
        assert limiter.hit("1.2.3.4", now=62) is None

    def test_clients_are_counted_separately(self):
        limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
        assert limiter.hit("1.1.1.1", now=0) is None
        assert limiter.hit("2.2.2.2", now=0) is None
        assert limiter.hit("1.1.1.1", now=1) is not None

    def test_client_ip_prefers_the_proxy_header(self):
        class Req:
            headers = {"x-forwarded-for": "203.0.113.9, 10.0.0.1"}
            client = type("C", (), {"host": "10.0.0.1"})()

        assert client_ip(Req()) == "203.0.113.9"


class TestDailyCeiling:
    def test_stops_at_the_limit_and_resets_the_next_day(self):
        counter = DailyCounter(limit=2)
        assert [counter.hit("2026-10-01") for _ in range(3)] == [True, True, False]
        assert counter.used_today == 2
        assert counter.hit("2026-10-02") is True
        assert counter.used_today == 1


@pytest.fixture
def client(monkeypatch):
    async def fake_single(text, tz_name=None):
        return ParsedEvent(title="Stub", start_time="2026-10-01T10:00:00+10:00")

    async def fake_is_multiple(text):
        return False

    monkeypatch.setattr(main.event_parser, "parse_event_text", fake_single)
    monkeypatch.setattr(main.event_parser, "is_multiple_events", fake_is_multiple)
    monkeypatch.setattr(main, "parse_rate_limiter", SlidingWindowRateLimiter(limit=3, window_seconds=60))
    monkeypatch.setattr(main, "daily_parse_counter", DailyCounter(limit=1000))
    return TestClient(main.app)


def parse(client, text="Lunch tomorrow at 1pm", ip="203.0.113.5"):
    return client.post("/create_event", json={"text": text}, headers={"x-forwarded-for": ip})


class TestParseEndpoint:
    def test_overlong_text_is_rejected_before_reaching_the_llm(self, client):
        response = parse(client, text="x" * (MAX_EVENT_TEXT_CHARS + 1))
        assert response.status_code == 422

    def test_text_at_the_limit_is_accepted(self, client):
        assert parse(client, text="x" * MAX_EVENT_TEXT_CHARS).status_code == 200

    def test_repeated_requests_are_throttled_per_caller(self, client):
        for _ in range(3):
            assert parse(client).status_code == 200

        throttled = parse(client)
        assert throttled.status_code == 429
        assert int(throttled.headers["retry-after"]) >= 1

        # A different caller is unaffected.
        assert parse(client, ip="198.51.100.7").status_code == 200

    def test_the_days_ceiling_stops_everyone(self, client, monkeypatch):
        monkeypatch.setattr(main, "daily_parse_counter", DailyCounter(limit=1))
        assert parse(client, ip="203.0.113.10").status_code == 200
        # A fresh caller, within its own per-minute allowance, is still refused.
        assert parse(client, ip="203.0.113.11").status_code == 429


class TestParseFailures:
    @pytest.mark.parametrize(
        "error, status, message",
        [
            ("NoEventFound", 422, main.NO_EVENT_MESSAGE),
            ("ParserUnavailable", 503, main.PARSER_UNAVAILABLE_MESSAGE),
        ],
    )
    def test_failures_are_reported_not_invented(self, client, monkeypatch, error, status, message):
        from backend.services import parse_errors

        async def failing(text, tz_name=None):
            raise getattr(parse_errors, error)()

        monkeypatch.setattr(main.event_parser, "parse_event_text", failing)
        response = parse(client)
        assert response.status_code == status
        assert response.json()["detail"] == message

    def test_the_parser_keeps_text_up_to_the_api_limit(self):
        from backend.services.intelligent_parser import IntelligentEventParser

        text = "Lunch on Friday at 1pm. " * 60  # about 1,400 characters
        sanitized = IntelligentEventParser._sanitize_input(None, text)
        assert len(sanitized) > 1000
