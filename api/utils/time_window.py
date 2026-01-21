from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
from typing import Tuple

UTC = ZoneInfo("UTC")

def get_daily_window_utc(day: str, *, cutoff_hour: int = 6, tz_name: str | None = None) -> Tuple[datetime, datetime]:
    """
    Ventana oficial del ciclo: [day 06:00 Europe/Madrid, next_day 06:00 Europe/Madrid) expresada en UTC.
    day: YYYY-MM-DD (día de ciclo)
    """
    tz = ZoneInfo(tz_name or os.getenv("APP_TZ", "Europe/Madrid"))
    # start at cutoff in local tz
    start_local = datetime.fromisoformat(day).replace(tzinfo=tz, hour=cutoff_hour, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)
