"""Daily editorial priority, using Pakistan local calendar dates.

A user-requested topic wins over the scheduled automatic story for the
same day. An automatic draft already selected is preserved in queue/drafts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from post_store import load_json

LOCAL = ZoneInfo("Asia/Karachi")


def local_date(value: str) -> str:
    timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(LOCAL).date().isoformat()


def today_local(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.astimezone(LOCAL).date().isoformat()


def manual_requests_on_day(requests_dir: Path, day: str) -> list[dict]:
    """A pending request also reserves its day; broken sources never fake a draft."""
    requests = []
    for path in requests_dir.glob("*.json") if requests_dir.is_dir() else []:
        try:
            item = load_json(path, {})
            if isinstance(item, dict) and item.get("priority") == "user_requested" and \
               item.get("requested_at") and local_date(item["requested_at"]) == day:
                requests.append(item)
        except (ValueError, OSError, TypeError):
            continue
    return requests


def automatic_ready_on_day(drafts_dir: Path, day: str) -> bool:
    """Prevent duplicate scheduled drafts for the same local calendar day."""
    for path in drafts_dir.glob("*.json") if drafts_dir.is_dir() else []:
        try:
            item = load_json(path, {})
            if (isinstance(item, dict) and item.get("origin") == "automatic"
                    and item.get("created_at") and local_date(item["created_at"]) == day):
                return True
        except (ValueError, OSError, TypeError):
            continue
    return False
