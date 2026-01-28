from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from services.live_events_multisource import LiveEventsMultiSource
except ImportError:
    from api.services.live_events_multisource import LiveEventsMultiSource

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
    Ingest events for a day using free alternative APIs (ESPN, etc)
    No API_SPORTS_KEY needed - uses LiveEventsMultiSource
    """
    if day is None:
        day = date.today().isoformat()

    base_path = API_DATA_DIR / "events" / day
    base_path.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {"day": day, "sports": []}
    
    multisource = LiveEventsMultiSource()

    for sport in SUPPORTED_SPORTS:
        out_file = base_path / f"{sport}.json"
        
        if out_file.exists() and not force:
            summary["sports"].append(IngestResult(sport, day, "skipped", str(out_file), None).__dict__)
            continue

        try:
            # Get events from live multisource (ESPN + alternatives)
            events = multisource.get_live_events(sport, day)
            
            # events is already a dict with response/results structure
            if isinstance(events, dict):
                payload = events
            else:
                payload = {
                    "results": len(events) if events else 0,
                    "response": events or [],
                    "source": "live_events_multisource",
                    "status": "success"
                }
            
            out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            results = payload.get("results", 0)
            logger.info(f"Ingested {results} events for {sport} on {day}")
            
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
            payload = {"results": 0, "response": [], "errors": {"message": msg}, "source": "live_events_multisource"}
            try:
                out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            summary["sports"].append(IngestResult(sport, day, "error", str(out_file), 0).__dict__)

    return summary


if __name__ == "__main__":
    print(json.dumps(ingest_events_for_day(), ensure_ascii=False, indent=2))
