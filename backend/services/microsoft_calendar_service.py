"""Microsoft Outlook / Graph calendar integration for Prompt2Cal."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from dotenv import load_dotenv

from ..models.event_models import ParsedEvent

load_dotenv()

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
DEFAULT_SCOPES = [
    "openid",
    "offline_access",
    "User.Read",
    "Calendars.ReadWrite",
]


class MicrosoftCalendarService:
    def __init__(self) -> None:
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.CLIENT_ID = os.getenv("MS_CLIENT_ID")
        self.CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
        self.TENANT_ID = os.getenv("MS_TENANT_ID", "common")
        self.REDIRECT_URI = os.getenv(
            "MS_REDIRECT_URI",
            "http://localhost:8000/auth/microsoft/callback",
        )
        self.SCOPES = DEFAULT_SCOPES

    def _token_file(self, user_id: Optional[str]) -> str:
        if user_id:
            tokens_dir = os.path.join(self.BASE_DIR, "user_tokens")
            os.makedirs(tokens_dir, exist_ok=True)
            return os.path.join(tokens_dir, f"ms_{user_id}.json")
        return os.path.join(self.BASE_DIR, "ms_token.json")

    def _auth_base(self) -> str:
        return f"https://login.microsoftonline.com/{self.TENANT_ID}/oauth2/v2.0"

    def _require_client_config(self) -> None:
        if not self.CLIENT_ID or not self.CLIENT_SECRET:
            raise Exception(
                "Microsoft OAuth credentials not found. "
                "Set MS_CLIENT_ID and MS_CLIENT_SECRET in your .env file."
            )

    async def get_auth_url(self, user_id: Optional[str] = None) -> str:
        self._require_client_config()
        params = {
            "client_id": self.CLIENT_ID,
            "response_type": "code",
            "redirect_uri": self.REDIRECT_URI,
            "response_mode": "query",
            "scope": " ".join(self.SCOPES),
            "state": user_id or "",
            "prompt": "select_account",
        }
        return f"{self._auth_base()}/authorize?{urlencode(params)}"

    async def handle_auth_callback(self, code: str, user_id: Optional[str] = None) -> None:
        self._require_client_config()
        data = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "code": code,
            "redirect_uri": self.REDIRECT_URI,
            "grant_type": "authorization_code",
            "scope": " ".join(self.SCOPES),
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self._auth_base()}/token", data=data)
            if response.status_code >= 400:
                logger.error("Microsoft token exchange failed: %s", response.text)
                raise Exception(f"Microsoft authentication failed: {response.text}")
            token_payload = response.json()

        expires_in = int(token_payload.get("expires_in", 3600))
        token_data = {
            "access_token": token_payload.get("access_token"),
            "refresh_token": token_payload.get("refresh_token"),
            "token_type": token_payload.get("token_type", "Bearer"),
            "scope": token_payload.get("scope"),
            "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)).isoformat(),
            "auth_timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "microsoft",
        }
        token_file = self._token_file(user_id)
        with open(token_file, "w", encoding="utf-8") as handle:
            json.dump(token_data, handle)
        logger.info("Microsoft Calendar authentication completed for user: %s", user_id)

    def _load_token(self, user_id: Optional[str]) -> Optional[Dict]:
        token_file = self._token_file(user_id)
        if not os.path.exists(token_file):
            return None
        try:
            with open(token_file, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception as exc:
            logger.error("Failed to load Microsoft token for %s: %s", user_id, exc)
            return None

    def _save_token(self, user_id: Optional[str], token_data: Dict) -> None:
        token_file = self._token_file(user_id)
        with open(token_file, "w", encoding="utf-8") as handle:
            json.dump(token_data, handle)

    async def _ensure_access_token(self, user_id: Optional[str]) -> str:
        token_data = self._load_token(user_id)
        if not token_data or not token_data.get("access_token"):
            raise Exception("Microsoft Calendar is not connected. Please authenticate first.")

        auth_timestamp = token_data.get("auth_timestamp")
        if auth_timestamp:
            try:
                auth_date = datetime.fromisoformat(auth_timestamp.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - auth_date >= timedelta(days=14):
                    os.remove(self._token_file(user_id))
                    raise Exception(
                        "Microsoft authentication expired after 14 days. Please reconnect."
                    )
            except ValueError:
                pass

        expires_at = token_data.get("expires_at")
        needs_refresh = True
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                needs_refresh = datetime.now(timezone.utc) >= expiry
            except ValueError:
                needs_refresh = True

        if needs_refresh:
            refresh_token = token_data.get("refresh_token")
            if not refresh_token:
                raise Exception("Microsoft session expired. Please reconnect Microsoft Calendar.")
            self._require_client_config()
            data = {
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "scope": " ".join(self.SCOPES),
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self._auth_base()}/token", data=data)
                if response.status_code >= 400:
                    logger.error("Microsoft token refresh failed: %s", response.text)
                    raise Exception("Failed to refresh Microsoft Calendar session. Please reconnect.")
                refreshed = response.json()

            expires_in = int(refreshed.get("expires_in", 3600))
            token_data["access_token"] = refreshed.get("access_token")
            if refreshed.get("refresh_token"):
                token_data["refresh_token"] = refreshed["refresh_token"]
            token_data["expires_at"] = (
                datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
            ).isoformat()
            self._save_token(user_id, token_data)

        return token_data["access_token"]

    async def _graph_request(
        self,
        method: str,
        path: str,
        user_id: Optional[str],
        json_body: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        access_token = await self._ensure_access_token(user_id)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{GRAPH_BASE}{path}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                json=json_body,
                params=params,
            )
            if response.status_code >= 400:
                logger.error("Graph API error %s %s: %s", method, path, response.text)
                raise Exception(f"Microsoft Graph request failed: {response.text}")
            if response.status_code == 204 or not response.content:
                return {}
            return response.json()

    def is_authenticated(self, user_id: Optional[str] = None) -> bool:
        token_data = self._load_token(user_id)
        if not token_data:
            return False
        return bool(token_data.get("access_token") or token_data.get("token"))

    def logout(self, user_id: Optional[str] = None) -> bool:
        token_file = self._token_file(user_id)
        if os.path.exists(token_file):
            os.remove(token_file)
            logger.info("Removed Microsoft token for user: %s", user_id)
            return True
        return False

    @staticmethod
    def _split_datetime(value: str) -> tuple[str, str]:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if hasattr(dt.tzinfo, "zone") and getattr(dt.tzinfo, "zone"):
            return dt.replace(tzinfo=None).isoformat(timespec="seconds"), dt.tzinfo.zone  # type: ignore[attr-defined]
        # Offset-only timestamps: normalize to UTC for Graph compatibility
        dt_utc = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        return dt_utc.replace(tzinfo=None).isoformat(timespec="seconds"), "UTC"

    def _build_event_body(self, parsed_event: ParsedEvent) -> Dict:
        start_dt, start_tz = self._split_datetime(parsed_event.start_time)
        end_dt, end_tz = self._split_datetime(parsed_event.end_time)
        body: Dict = {
            "subject": parsed_event.title,
            "start": {"dateTime": start_dt, "timeZone": start_tz},
            "end": {"dateTime": end_dt, "timeZone": end_tz},
        }
        if parsed_event.location:
            body["location"] = {"displayName": parsed_event.location}
        if parsed_event.notes:
            body["body"] = {"contentType": "Text", "content": parsed_event.notes}
        if getattr(parsed_event, "attendees", None):
            attendees = []
            seen = set()
            for email in parsed_event.attendees:
                if not email:
                    continue
                cleaned = email.strip().lower()
                if not cleaned or cleaned in seen:
                    continue
                seen.add(cleaned)
                attendees.append(
                    {
                        "emailAddress": {"address": cleaned},
                        "type": "required",
                    }
                )
            if attendees:
                body["attendees"] = attendees
        if getattr(parsed_event, "add_conference", False):
            body["isOnlineMeeting"] = True
            body["onlineMeetingProvider"] = "teamsForBusiness"
        recurrence = self._build_recurrence(parsed_event)
        if recurrence:
            body["recurrence"] = recurrence
        return body

    def _build_recurrence(self, parsed_event: ParsedEvent) -> Optional[Dict]:
        recurrence_type = str(getattr(parsed_event, "recurrence_type", "none") or "none").lower()
        if recurrence_type in ("", "none"):
            return None
        start_dt = datetime.fromisoformat(parsed_event.start_time.replace("Z", "+00:00"))
        interval = getattr(parsed_event, "recurrence_interval", 1) or 1
        pattern_type = {
            "daily": "daily",
            "weekly": "weekly",
            "monthly": "absoluteMonthly",
            "yearly": "absoluteYearly",
        }.get(recurrence_type)
        if not pattern_type:
            return None

        pattern: Dict = {"type": pattern_type, "interval": interval}
        if recurrence_type == "weekly":
            pattern["daysOfWeek"] = [start_dt.strftime("%A").lower()]
        if recurrence_type == "monthly":
            pattern["dayOfMonth"] = start_dt.day
        if recurrence_type == "yearly":
            pattern["dayOfMonth"] = start_dt.day
            pattern["month"] = start_dt.month

        range_body: Dict = {
            "type": "noEnd",
            "startDate": start_dt.date().isoformat(),
        }
        end_date = getattr(parsed_event, "end_date", None)
        end_after = getattr(parsed_event, "end_after_count", None) or getattr(
            parsed_event, "recurrence_count", None
        )
        if end_date:
            try:
                end_dt = datetime.fromisoformat(str(end_date).replace("Z", "+00:00"))
                range_body = {
                    "type": "endDate",
                    "startDate": start_dt.date().isoformat(),
                    "endDate": end_dt.date().isoformat(),
                }
            except ValueError:
                pass
        elif end_after and int(end_after) > 0:
            range_body = {
                "type": "numbered",
                "startDate": start_dt.date().isoformat(),
                "numberOfOccurrences": int(end_after),
            }

        return {"pattern": pattern, "range": range_body}

    async def get_calendars(
        self, user_id: Optional[str] = None, writable_only: bool = True
    ) -> List[Dict]:
        payload = await self._graph_request("GET", "/me/calendars", user_id)
        calendars = []
        for calendar in payload.get("value", []):
            can_edit = calendar.get("canEdit", False)
            if writable_only and not can_edit:
                continue
            calendars.append(
                {
                    "id": calendar.get("id"),
                    "summary": calendar.get("name") or "Untitled Calendar",
                    "primary": bool(calendar.get("isDefaultCalendar")),
                    "accessRole": "owner" if can_edit else "reader",
                    "provider": "microsoft",
                }
            )
        calendars.sort(key=lambda item: (not item["primary"], item["summary"].lower()))
        return calendars

    async def create_calendar_event(
        self,
        parsed_event: ParsedEvent,
        user_id: Optional[str] = None,
        original_text: Optional[str] = None,
        calendar_id: Optional[str] = None,
    ) -> str:
        if not parsed_event.title:
            raise Exception("Event title is required")
        if not parsed_event.start_time or not parsed_event.end_time:
            raise Exception("Event start and end times are required")

        body = self._build_event_body(parsed_event)
        path = f"/me/calendars/{calendar_id}/events" if calendar_id else "/me/events"
        created = await self._graph_request("POST", path, user_id, json_body=body)

        # Best-effort web link
        web_link = created.get("webLink") or ""
        if not web_link:
            event_id = created.get("id")
            web_link = f"https://outlook.office.com/calendar/item/{event_id}" if event_id else ""
        logger.info("Microsoft event created: %s", created.get("id"))
        return web_link

    async def check_conflicts(
        self,
        start_time: str,
        end_time: str,
        user_id: Optional[str] = None,
        calendar_id: Optional[str] = None,
        buffer_minutes: int = 0,
    ) -> List[Dict]:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        if buffer_minutes:
            start_dt -= timedelta(minutes=buffer_minutes)
            end_dt += timedelta(minutes=buffer_minutes)

        params = {
            "startDateTime": start_dt.isoformat().replace("+00:00", "Z"),
            "endDateTime": end_dt.isoformat().replace("+00:00", "Z"),
        }
        path = (
            f"/me/calendars/{calendar_id}/calendarView"
            if calendar_id
            else "/me/calendarView"
        )
        payload = await self._graph_request("GET", path, user_id, params=params)
        conflicts = []
        for item in payload.get("value", []):
            conflicts.append(
                {
                    "id": item.get("id"),
                    "summary": item.get("subject"),
                    "start": item.get("start", {}).get("dateTime"),
                    "end": item.get("end", {}).get("dateTime"),
                    "htmlLink": item.get("webLink"),
                }
            )
        return conflicts
