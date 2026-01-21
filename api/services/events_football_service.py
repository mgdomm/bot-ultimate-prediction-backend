import requests
from pathlib import Path
from datetime import datetime

from utils.time_window import get_daily_window_utc
from services.env import get_env

API_BASE_URL = "https://v3.football.api-sports.io"

def fetch_football_events():
    env = get_env()
    api_key = env["API_SPORTS_KEY"]

    start_utc, end_utc = get_daily_window_utc()

    # API-Football trabaja mejor por DATE
    date_str = start_utc.date().isoformat()

    params = {
        "date": date_str
    }

    headers = {
        "x-apisports-key": api_key
    }

    response = requests.get(
        f"{API_BASE_URL}/fixtures",
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()
    payload = response.json()

    spain_date = date_str
    base_path = Path("data/events") / spain_date
    base_path.mkdir(parents=True, exist_ok=True)

    output_file = base_path / "football.json"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(response.text)

    return {
        "events": payload.get("results", 0),
        "file": str(output_file),
        "date": date_str,
    }
