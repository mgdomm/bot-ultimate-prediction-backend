from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from services.api_sports_client import ApiSportsClient
    from services.api_sports_hosts import SPORT_BASE_URL
except ModuleNotFoundError:
    from api.services.api_sports_client import ApiSportsClient  # type: ignore
    from api.services.api_sports_hosts import SPORT_BASE_URL  # type: ignore


# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


EVENTS_ENDPOINT_BY_SPORT: Dict[str, str] = {
    # API-Football
    "football": "/fixtures",

    # Most API-Sports products
    "basketball": "/games",
    "baseball": "/games",
    "hockey": "/games",
    "handball": "/games",
    "volleyball": "/games",
    "rugby": "/games",
    "afl": "/games",

    # Panel-specific
    "nba": "/games",
    "nfl": "/games",  # (host is american-football)

    # Others
    "mma": "/fights",
    "formula-1": "/races",
}


@dataclass(frozen=True)
class IngestResult:
    sport: str
    day: str
    status: str  # created | skipped
    file: str
    results: Optional[int] = None


def ingest_events_for_day(day: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    base_path = API_DATA_DIR / "events" / day
    base_path.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {"day": day, "sports": []}

    stop_due_to_rate_limit = False

    for sport in sorted(SPORT_BASE_URL.keys()):
        endpoint = EVENTS_ENDPOINT_BY_SPORT.get(sport)
        if not endpoint:
            summary["sports"].append(IngestResult(sport, day, "skipped", "", None).__dict__)
            continue

        out_file = base_path / f"{sport}.json"
        if out_file.exists() and not force:
            summary["sports"].append(IngestResult(sport, day, "skipped", str(out_file), None).__dict__)
            continue

        if stop_due_to_rate_limit:
            summary["sports"].append(IngestResult(sport, day, "skipped_rate_limited", str(out_file), 0).__dict__)
            continue

        client = ApiSportsClient(sport)
        try:
            payload = client.get(endpoint, params={"date": day})
            out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            summary["sports"].append(
                IngestResult(
                    sport=sport,
                    day=day,
                    status="created",
                    file=str(out_file),
                    results=payload.get("results") if isinstance(payload, dict) else None,
                ).__dict__
            )
        except Exception as err:
            msg = str(err)
            payload = {"results": 0, "response": [], "errors": {"message": msg}}
            try:
                out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            summary["sports"].append(IngestResult(sport, day, "error", str(out_file), 0).__dict__)

            # If daily quota is exhausted, stop trying other sports to avoid wasting calls.
            if "reached the request limit for the day" in msg:
                stop_due_to_rate_limit = True

    return summary


if __name__ == "__main__":
    print(json.dumps(ingest_events_for_day(), ensure_ascii=False, indent=2))
