"""Calendar token storage keyed by server-issued sessions, plus OAuth sign-in state.

A session is minted by the server only when a sign-in completes, and is handed
to the extension that started it through its chrome.identity redirect URL. No
caller can choose, predict or reuse the session that another user's calendar
tokens are stored under, and session strings are strictly validated before
they are used to build a file path.

Tokens live in TOKEN_STORAGE_DIR (a Cloud Storage volume in production, so
they survive restarts and are shared between instances), or backend/user_tokens
locally.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import time
from typing import Dict, Optional
from urllib.parse import urlsplit

PROVIDERS = ("google", "microsoft")
PENDING_STATE_TTL_SECONDS = 600

_DEFAULT_TOKEN_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_tokens"
)
_SESSION_PATTERN = re.compile(r"^s_[A-Za-z0-9_-]{43}$")
_STATE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
_EXTENSION_REDIRECT_HOST = re.compile(r"^[a-p]{32}\.chromiumapp\.org$")
_PENDING_PREFIX = "pending_"


class InvalidSession(ValueError):
    """The caller did not present a session this server could have issued."""


def token_dir() -> str:
    path = os.getenv("TOKEN_STORAGE_DIR") or _DEFAULT_TOKEN_DIR
    os.makedirs(path, exist_ok=True)
    return path


def is_valid_session(session: Optional[str]) -> bool:
    return isinstance(session, str) and bool(_SESSION_PATTERN.match(session))


def short_id(session: Optional[str]) -> str:
    """A log-safe prefix; the full session is a bearer secret."""
    return f"{session[:8]}..." if is_valid_session(session) else "<none>"


def token_path(provider: str, session: Optional[str]) -> str:
    if not is_valid_session(session):
        raise InvalidSession("Not signed in. Please connect your calendar.")
    prefix = "ms_" if provider == "microsoft" else ""
    return os.path.join(token_dir(), f"{prefix}{session}.json")


def start_session(previous_session: Optional[str] = None) -> str:
    """Mint a session for a completed sign-in.

    Tokens for providers connected under ``previous_session`` move to the new
    session, so connecting Outlook keeps Google connected. The old session is
    left empty, and a sign-in started with someone else's session never hands
    its result back to them.
    """
    session = "s_" + secrets.token_urlsafe(32)
    if is_valid_session(previous_session):
        for provider in PROVIDERS:
            old_path = token_path(provider, previous_session)
            if os.path.exists(old_path):
                os.replace(old_path, token_path(provider, session))
    return session


def is_allowed_redirect_uri(uri: Optional[str]) -> bool:
    """Only a Chrome extension's chrome.identity redirect URL may receive a session."""
    try:
        parts = urlsplit(uri or "")
        port = parts.port
    except ValueError:
        return False
    host = parts.hostname or ""
    if parts.scheme != "https" or parts.netloc != host or port or parts.fragment:
        return False
    expected_extension_id = os.getenv("CHROME_EXTENSION_ID")
    if expected_extension_id:
        return host == f"{expected_extension_id}.chromiumapp.org"
    return bool(_EXTENSION_REDIRECT_HOST.match(host))


def _pending_path(state: str) -> str:
    return os.path.join(token_dir(), f"{_PENDING_PREFIX}{state}.json")


def _sweep_expired_states() -> None:
    cutoff = time.time() - PENDING_STATE_TTL_SECONDS
    directory = token_dir()
    for name in os.listdir(directory):
        if not name.startswith(_PENDING_PREFIX):
            continue
        path = os.path.join(directory, name)
        try:
            if os.path.getmtime(path) < cutoff:
                os.remove(path)
        except OSError:
            pass


def create_pending_state(
    provider: str, redirect_uri: str, previous_session: Optional[str] = None
) -> str:
    """Record a sign-in in progress and return its single-use OAuth state."""
    _sweep_expired_states()
    state = secrets.token_urlsafe(32)
    pending = {
        "provider": provider,
        "redirect_uri": redirect_uri,
        "previous_session": previous_session if is_valid_session(previous_session) else None,
        "created_at": time.time(),
    }
    with open(_pending_path(state), "w", encoding="utf-8") as handle:
        json.dump(pending, handle)
    return state


def consume_pending_state(state: Optional[str], provider: str) -> Optional[Dict]:
    """Return and delete a sign-in's pending record, or None if it is unknown, used or expired."""
    if not isinstance(state, str) or not _STATE_PATTERN.match(state):
        return None
    path = _pending_path(state)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            pending = json.load(handle)
        # Whoever deletes the file owns the state, so a replayed callback fails.
        os.remove(path)
    except (OSError, ValueError):
        return None
    if pending.get("provider") != provider:
        return None
    if time.time() - float(pending.get("created_at", 0)) > PENDING_STATE_TTL_SECONDS:
        return None
    return pending
