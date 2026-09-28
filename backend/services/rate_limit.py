"""Per-client rate limiting for the endpoints that cost money to serve.

Parsing an event calls an LLM, and the API is public, so a script pointed at
the backend could run up a bill. The limiter keeps a short sliding window of
request times per client and refuses anything above the limit.

Counts are per instance. Cloud Run may run several, so the effective limit is
the configured one times the number of instances; that is plenty to stop a
runaway script, and it needs no shared state.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict, Optional

MAX_TRACKED_CLIENTS = 10_000


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = {}

    def hit(self, key: str, now: Optional[float] = None) -> Optional[int]:
        """Record a request.

        Returns None when the request is allowed, or the number of seconds the
        caller should wait before retrying.
        """
        now = time.monotonic() if now is None else now
        cutoff = now - self.window_seconds
        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= self.limit:
            return max(1, int(hits[0] + self.window_seconds - now) + 1)

        hits.append(now)
        self._forget_idle_clients(cutoff)
        return None

    def _forget_idle_clients(self, cutoff: float) -> None:
        """Keep memory flat on a long-lived instance."""
        if len(self._hits) <= MAX_TRACKED_CLIENTS:
            return
        for key in [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[key]


class DailyCounter:
    """A ceiling on how many paid calls the service makes in one UTC day.

    The per-caller limit does not stop abuse spread across many addresses, so
    this caps the total. It resets at midnight UTC and, like the rate limiter,
    counts per instance.
    """

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._day: Optional[str] = None
        self._count = 0

    def hit(self, today: Optional[str] = None) -> bool:
        """Record a call. Returns False once the day's ceiling is reached."""
        day = today or time.strftime("%Y-%m-%d", time.gmtime())
        if day != self._day:
            self._day, self._count = day, 0
        if self._count >= self.limit:
            return False
        self._count += 1
        return True

    @property
    def used_today(self) -> int:
        return self._count


def client_ip(request) -> str:
    """The caller's address, taken from the proxy header Cloud Run sets."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
