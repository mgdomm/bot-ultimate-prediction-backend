from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

def cycle_day_str(now: datetime | None = None, *, cutoff_hour: int = 6, tz_name: str | None = None) -> str:
    tz = ZoneInfo(tz_name or os.getenv("APP_TZ", "Europe/Madrid"))
    now = now.astimezone(tz) if now else datetime.now(tz)

    cutoff = now.replace(hour=cutoff_hour, minute=0, second=0, microsecond=0)
    if now < cutoff:
        now = now - timedelta(days=1)
    return now.date().isoformat()
