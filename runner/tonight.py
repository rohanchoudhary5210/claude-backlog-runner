"""Decide whether the owner approved ask-first tasks for tonight."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

DEFAULT_TZ = "Asia/Kolkata"
PHRASE = "tonight: go"


def _cutoff(now: int, tz: tzinfo) -> datetime:
    """18:00 local time of the previous day for runs before noon, else of the same day."""
    local = datetime.fromtimestamp(now, tz)
    day = local.date() - timedelta(days=1) if local.hour < 12 else local.date()
    return datetime(day.year, day.month, day.day, 18, tzinfo=tz)


def tonight_on(comments: list[dict], owner: str, now: int, tz: str = DEFAULT_TZ) -> bool:
    cutoff = _cutoff(now, ZoneInfo(tz))
    for c in comments:
        login = ((c.get("author") or {}).get("login") or "").lower()
        body = (c.get("body") or "").strip().lower()
        try:
            created = datetime.fromisoformat(c.get("createdAt", "").replace("Z", "+00:00"))
        except ValueError:
            continue
        if login == owner.lower() and body.startswith(PHRASE) and cutoff <= created <= datetime.fromtimestamp(now, timezone.utc):
            return True
    return False
