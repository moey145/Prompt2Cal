"""Keep users' event text out of the logs.

Event descriptions carry names, locations and appointments, and the privacy
policy promises that logs omit that content. Logs therefore record the size of
a value rather than the value itself, unless LOG_EVENT_CONTENT is set while
debugging locally.
"""

from __future__ import annotations

import os
from typing import Any


def content_logging_enabled() -> bool:
    return os.getenv("LOG_EVENT_CONTENT", "").strip().lower() in ("1", "true", "yes")


def safe(value: Any) -> str:
    """A log-safe stand-in for user-supplied text."""
    if value is None:
        return "<none>"
    text = str(value)
    if content_logging_enabled():
        return text
    return f"<{len(text)} chars>"
