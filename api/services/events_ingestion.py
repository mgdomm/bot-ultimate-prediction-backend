from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from services.api_sportsgameodds_client import SportsGameOddsClient  # type: ignore
except ImportError:
    from api.services.api_sportsgameodds_client import SportsGameOddsClient  # type: ignore

logger = logging.getLogger(__name__)

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"

def _env_sports() -> List[str]:
    """Return sports list from env (comma separated) defaulting to full SGO coverage."""
    raw = os.environ.get("SGO_EVENTS_SPORTS") or os.environ.get("EVENTS_SPORTS")
    if raw:
        return [s.strip().lower() for s in raw.split(",") if s.strip()]
    # Default full slate (8 deportes) para ingestión automática diaria
    return [
        "nba",
        "nfl",
        "nhl",
        "mlb",
        "college_basketball",
        "college_football",
        "soccer_champions",
        "soccer_mls",
    ]


@dataclass(frozen=True)
class IngestResult:
    sport: str
    day: str
    status: str  # created | skipped | error
    file: str
    results: Optional[int] = None


def _choose_team_name(team: Dict[str, Any]) -> str:
    names = team.get("names") if isinstance(team.get("names"), dict) else {}
    for key in ("medium", "long", "short"):
        val = names.get(key)
        if val:
            return str(val)
    # Fallback to bare teamID
    tid = team.get("teamID")
    return str(tid) if tid is not None else ""


def ingest_events_for_day(day: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """Ingest events for a day using SportsGameOdds (single source for picks)."""
    if day is None:
        day = date.today().isoformat()

    base_path = API_DATA_DIR / "events" / day
    base_path.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {"day": day, "sports": []}
    
    sports = _env_sports()

    client = SportsGameOddsClient()
    all_events = client.fetch_all_odds(day, force_refresh=force)  # cached; 1 req per sport max

    for sport in sports:
        out_file = base_path / f"{sport}.json"

        if out_file.exists() and not force:
            summary["sports"].append(IngestResult(sport, day, "skipped", str(out_file), None).__dict__)
            continue

        try:
            raw_events = all_events.get(sport, []) if isinstance(all_events, dict) else []
            cleaned = []

            for ev in raw_events if isinstance(raw_events, list) else []:
                if not isinstance(ev, dict):
                    continue

                status = ev.get("status") if isinstance(ev.get("status"), dict) else {}
                teams = ev.get("teams") if isinstance(ev.get("teams"), dict) else {}
                home = teams.get("home") if isinstance(teams.get("home"), dict) else {}
                away = teams.get("away") if isinstance(teams.get("away"), dict) else {}

                event_id = ev.get("eventID") or ev.get("eventId") or ev.get("id")
                if not event_id:
                    continue

                # Skip finished/cancelled
                if status.get("cancelled") or status.get("ended") or status.get("completed"):
                    continue

                start_time = status.get("startsAt") or ev.get("startTime")
                if not start_time:
                    continue

                cleaned.append({
                    "eventId": str(event_id),
                    "sport": sport,
                    "league": ev.get("leagueID") or ev.get("sportID") or ev.get("league"),
                    "startTime": start_time,
                    "status": {
                        "started": status.get("started"),
                        "completed": status.get("completed"),
                        "ended": status.get("ended"),
                        "cancelled": status.get("cancelled"),
                        "live": status.get("live"),
                        "delayed": status.get("delayed"),
                        "oddsPresent": status.get("oddsPresent"),
                        "oddsAvailable": status.get("oddsAvailable"),
                    },
                    "home": {
                        "id": home.get("teamID"),
                        "name": _choose_team_name(home),
                        "colors": home.get("colors") if isinstance(home.get("colors"), dict) else None,
                    },
                    "away": {
                        "id": away.get("teamID"),
                        "name": _choose_team_name(away),
                        "colors": away.get("colors") if isinstance(away.get("colors"), dict) else None,
                    },
                })

            payload = {
                "results": len(cleaned),
                "response": cleaned,
                "source": "sportsgameodds",
                "status": "success" if cleaned else "no_events",
            }

            out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            summary["sports"].append(
                IngestResult(
                    sport=sport,
                    day=day,
                    status="created",
                    file=str(out_file),
                    results=len(cleaned),
                ).__dict__
            )
        except Exception as err:
            logger.error(f"Error ingesting {sport}: {err}")
            msg = str(err)
            payload = {"results": 0, "response": [], "errors": {"message": msg}, "source": "sportsgameodds"}
            try:
                out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            summary["sports"].append(IngestResult(sport, day, "error", str(out_file), 0).__dict__)

    return summary


if __name__ == "__main__":
    print(json.dumps(ingest_events_for_day(), ensure_ascii=False, indent=2))
