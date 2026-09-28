"""The privacy policy promises logs omit event content; these tests hold us to it."""

import logging

import pytest

from backend.services import log_safety
from backend.services.log_safety import safe
from backend.services.multiple_event_detector import MultipleEventDetector


@pytest.fixture(autouse=True)
def content_logging_off(monkeypatch):
    monkeypatch.delenv("LOG_EVENT_CONTENT", raising=False)


def test_text_is_replaced_by_its_size():
    assert safe("Dentist Thursday 10am") == "<21 chars>"
    assert safe(None) == "<none>"


def test_content_can_be_restored_for_local_debugging(monkeypatch):
    monkeypatch.setenv("LOG_EVENT_CONTENT", "true")
    assert safe("Dentist Thursday 10am") == "Dentist Thursday 10am"


def test_detector_does_not_log_the_users_text(caplog):
    text = "Lunch with Dr Okonkwo about the biopsy results Thursday 10am"
    import asyncio

    with caplog.at_level(logging.INFO):
        asyncio.run(MultipleEventDetector().is_multiple_events(text))

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert logged, "expected the detector to log something"
    for fragment in ("Okonkwo", "biopsy", "Lunch"):
        assert fragment not in logged
