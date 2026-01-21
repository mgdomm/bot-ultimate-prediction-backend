import os
import json
import requests
from datetime import datetime

API_KEY = os.getenv("API_SPORTS_KEY")

# DF_DIAG_API_SPORTS_KEY
try:
    _k = API_KEY
except NameError:
    _k = None
print({
  'diag': 'api_sports_key',
  'present': bool(_k),
  'len': (len(_k) if _k else 0)
}, flush=True)
BASE_URL = "https://v3.football.api-sports.io/odds"
HEADERS = {
    "x-apisports-key": API_KEY
}

SPORT = "football"

def ingest_odds_for_today():
    today = datetime.now().strftime("%Y-%m-%d")

    events_path = f"data/events/{today}/{SPORT}_normalized.json"
    odds_dir = f"data/odds/{today}"
    odds_file = f"{odds_dir}/{SPORT}.json"

    if not os.path.exists(events_path):
        raise FileNotFoundError(f"No events file found: {events_path}")

    os.makedirs(odds_dir, exist_ok=True)

    with open(events_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    fixture_ids = [event["eventId"] for event in events]

    all_odds = []

    print(f"[ODDS] Fixtures to request: {len(fixture_ids)}")

    for idx, fixture_id in enumerate(fixture_ids, start=1):
        print(f"[ODDS] ({idx}/{len(fixture_ids)}) Fixture {fixture_id}")

        try:
            response = requests.get(
                BASE_URL,
                headers=HEADERS,
                params={"fixture": fixture_id},
                timeout=15
            )
        except Exception as e:
            all_odds.append({
                "fixture": fixture_id,
                "error": str(e),
                "response": None
            })
            continue

        if response.status_code != 200:
            all_odds.append({
                "fixture": fixture_id,
                "error": response.status_code,
                "response": None
            })
            continue

        all_odds.append({
            "fixture": fixture_id,
            "response": response.json()
        })

    with open(odds_file, "w", encoding="utf-8") as f:
        json.dump(all_odds, f, indent=2, ensure_ascii=False)

    return {
        "date": today,
        "fixtures_requested": len(fixture_ids),
        "odds_file": odds_file
}
