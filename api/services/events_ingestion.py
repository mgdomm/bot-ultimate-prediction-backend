from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from services.api_theodds_client import TheOddsAPIClient
except ImportError:
    from api.services.api_theodds_client import TheOddsAPIClient

logger = logging.getLogger(__name__)

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"

# Sports que traemos eventos (usando APIs alternativas FREE)
SUPPORTED_SPORTS = [
    "football",
    "soccer", 
    "basketball",
    "nba",
    "rugby",
    "nfl",
    "american-football",
    "hockey",
    "baseball",
    "tennis",
    "afl",
]


@dataclass(frozen=True)
class IngestResult:
    sport: str
    day: str
    status: str  # created | skipped | error
    file: str
    results: Optional[int] = None


def ingest_events_for_day(day: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """
    Ingest events for a day using The Odds API (primary source for betting odds).
    ESPN is used ONLY for live score updates (in display enrichment).
    """
    if day is None:
        day = date.today().isoformat()

    base_path = API_DATA_DIR / "events" / day
    base_path.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {"day": day, "sports": []}
    
    theodds = TheOddsAPIClient()

    for sport in SUPPORTED_SPORTS:
        out_file = base_path / f"{sport}.json"
        
        if out_file.exists() and not force:
            summary["sports"].append(IngestResult(sport, day, "skipped", str(out_file), None).__dict__)
            continue

        try:
            # PRIMARY SOURCE: Get events from The Odds API with real betting odds
            logger.info(f"Fetching events for {sport} from The Odds API...")
            odds_events = theodds.get_events_with_odds(sport, day)
            odds_list = odds_events.get("events", [])
            
            if odds_list:
                # Use The Odds API as primary source
                payload = {
                    "results": len(odds_list),
                    "response": odds_list,
                    "source": "theodds_api_primary",
                    "status": "success"
                }
                results = len(odds_list)
                logger.info(f"✓ The Odds API: {results} events for {sport}")
            else:
                # No events found - this is normal for some sports/dates
                logger.info(f"ℹ No events found for {sport} on {day}")
                payload = {
                    "results": 0,
                    "response": [],
                    "source": "theodds_api_primary",
                    "status": "no_events"
                }
                results = 0
            
            out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            
            summary["sports"].append(
                IngestResult(
                    sport=sport,
                    day=day,
                    status="created",
                    file=str(out_file),
                    results=results,
                ).__dict__
            )
        except Exception as err:
            logger.error(f"Error ingesting {sport}: {err}")
            msg = str(err)
            payload = {"results": 0, "response": [], "errors": {"message": msg}, "source": "theodds_api_primary"}
            try:
                out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            summary["sports"].append(IngestResult(sport, day, "error", str(out_file), 0).__dict__)

    return summary


if __name__ == "__main__":
    print(json.dumps(ingest_events_for_day(), ensure_ascii=False, indent=2))
