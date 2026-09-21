"""Unit tests for single vs multiple event detection."""

import asyncio

import pytest

from backend.services.multiple_event_detector import MultipleEventDetector


def is_multiple(text):
    return asyncio.run(MultipleEventDetector().is_multiple_events(text))


@pytest.mark.parametrize(
    "text",
    [
        "Dentist Thursday 10am, then team standup every Monday at 9am for 3 weeks",
        "Dentist Thursday 10am, team standup every Monday at 9am",
        "Team standup every Monday at 9am. Dentist Thursday at 10am",
        "Yoga every Tuesday at 6pm then dinner with Sam at 8pm",
    ],
)
def test_one_off_event_alongside_series_is_multiple(text):
    assert is_multiple(text)


@pytest.mark.parametrize(
    "text",
    [
        "Team standup every Monday at 9am for 3 weeks",
        "Team meeting every Monday and Wednesday at 9am",
        "Standup every Monday at 9am, and Wednesday at 5pm",
        "Weekly review every Friday at 4pm, remind me at 3:30pm",
        "Weekly review every Friday at 4pm, ending at 5pm",
        "Gym every Monday at 6:30am to 8am",
        "Standup every Monday at 9am. Notes: bring laptop and prep slides by 8am",
    ],
)
def test_single_recurring_series_stays_single(text):
    assert not is_multiple(text)
