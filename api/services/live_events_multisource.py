"""
DF_LIVE_EVENTS_MULTISOURCE: Agregador de eventos live desde múltiples APIs

Soporta:
- ESPN (Soccer, Rugby, NFL) - sin autenticación
- Alternativas (NBA, NHL, Handball, Volleyball, AFL) - sin autenticación
- SofaScore (Odds para TODOS los deportes) - sin autenticación, completamente gratis
- Fallback a snapshots estáticos
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

try:
    from api.services.api_alternatives_client import AlternativeApisClient
    from api.services.api_espn_client import ESPNClient
    from api.services.api_sofascore_client import SofaScoreClient
except ModuleNotFoundError:
    from api_alternatives_client import AlternativeApisClient
    from api_espn_client import ESPNClient
    from api_sofascore_client import SofaScoreClient


class LiveEventsMultiSource:
    """Aggregator for live events from multiple sources by sport"""
    
    # Sport -> data source mapping
    SPORT_SOURCES = {
        # ESPN sources (Phase 2)
        "football": "espn",  # Soccer
        "soccer": "espn",
        "rugby": "espn",
        "rugby-league": "espn",
        "american-football": "espn",
        "nfl": "espn",
        
        # Alternative sources (Phase 1)
        "basketball": "alternatives",
        "hockey": "alternatives",
        "handball": "alternatives",
        "volleyball": "alternatives",
        "afl": "alternatives",
        
        # Fallback (snapshots only)
        "tennis": "snapshot",
        "baseball": "snapshot",
        "mma": "snapshot",
        "f1": "snapshot",
    }
    
    @staticmethod
    def get_live_events(sport: str, date: str) -> Dict[str, Any]:
        """
        Get live events for a sport, trying sources in order:
        1. Primary source (ESPN/alternatives)
        2. Fallback to snapshots
        
        Returns: {"live_by_id": {eventId: liveData, ...}, "source": "espn"|"alternatives"|"snapshot", "error": optional}
        """
        sport_lower = sport.lower()
        source_type = LiveEventsMultiSource.SPORT_SOURCES.get(sport_lower, "snapshot")
        
        if source_type == "espn":
            return LiveEventsMultiSource._get_from_espn(sport_lower, date)
        elif source_type == "alternatives":
            return LiveEventsMultiSource._get_from_alternatives(sport_lower, date)
        else:
            return LiveEventsMultiSource._get_from_snapshot(sport_lower, date)
    
    @staticmethod
    def get_events_with_odds(sport: str, date: str) -> Dict[str, Any]:
        """
        Get events for a sport WITH odds from SofaScore
        SofaScore is completely free and supports all 12 sports with betting odds
        
        Returns: {"events": [{eventId, sport, home, away, startTime, status, odds, live}], "source": "sofascore", "count": int}
        """
        try:
            sofascore = SofaScoreClient()
            result = sofascore.get_events_with_odds(sport, date)
            
            # Enrich with live data if available
            if result.get("events"):
                live_result = LiveEventsMultiSource.get_live_events(sport, date)
                live_by_id = live_result.get("live_by_id", {})
                
                for event in result["events"]:
                    event_id = event.get("eventId")
                    if event_id in live_by_id:
                        event["live"] = live_by_id[event_id]
            
            return result
        except Exception as e:
            print(f"[multisource] SofaScore failed for {sport}: {e}")
            return {
                "events": [],
                "source": "sofascore",
                "error": str(e),
            }
    
    @staticmethod
    def _get_from_espn(sport: str, date: str) -> Dict[str, Any]:
        """Fetch from ESPN APIs (Soccer, Rugby, NFL)"""
        try:
            events = ESPNClient.get_live_events(sport, date)
            
            # Normalize to live_by_id format
            live_by_id = {}
            for event in events:
                event_id = event.get("eventId")
                if event_id:
                    live_by_id[str(event_id)] = event.get("live", {})
            
            return {
                "live_by_id": live_by_id,
                "source": "espn",
                "count": len(events),
            }
        except Exception as e:
            print(f"[multisource] ESPN failed for {sport}: {e}")
            return {
                "live_by_id": {},
                "source": "espn",
                "error": str(e),
            }
    
    @staticmethod
    def _get_from_alternatives(sport: str, date: str) -> Dict[str, Any]:
        """Fetch from alternative APIs (balldontlie, NHL stats, OpenLigaDB, Squiggle)"""
        try:
            events = AlternativeApisClient.get_live_events(sport, date)
            
            # Normalize to live_by_id format
            live_by_id = {}
            for event in events:
                event_id = event.get("eventId")
                if event_id:
                    live_by_id[str(event_id)] = event.get("live", {})
            
            return {
                "live_by_id": live_by_id,
                "source": "alternatives",
                "count": len(events),
            }
        except Exception as e:
            print(f"[multisource] alternatives failed for {sport}: {e}")
            return {
                "live_by_id": {},
                "source": "alternatives",
                "error": str(e),
            }
    
    @staticmethod
    def _get_from_snapshot(sport: str, date: str) -> Dict[str, Any]:
        """Fallback to local event snapshots"""
        try:
            snapshot_path = Path(f"api/data/events/{date}")
            if not snapshot_path.exists():
                return {
                    "live_by_id": {},
                    "source": "snapshot",
                    "error": "No snapshots available",
                }
            
            # Try to load sport-specific snapshot
            live_by_id = {}
            
            # Look for files matching sport pattern
            for event_file in snapshot_path.glob(f"*{sport}*.json"):
                try:
                    with open(event_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            event_id = data.get("eventId") or data.get("id")
                            if event_id:
                                live_by_id[str(event_id)] = data.get("live", {})
                except Exception:
                    pass
            
            # Fallback: load all and filter
            if not live_by_id:
                for event_file in snapshot_path.glob("*.json"):
                    try:
                        with open(event_file, "r", encoding="utf-8") as f:
                            events = json.load(f)
                            if isinstance(events, list):
                                for event in events:
                                    if event.get("sport", "").lower() == sport.lower():
                                        event_id = event.get("eventId")
                                        if event_id:
                                            live_by_id[str(event_id)] = event.get("live", {})
                    except Exception:
                        pass
            
            return {
                "live_by_id": live_by_id,
                "source": "snapshot",
                "count": len(live_by_id),
            }
        except Exception as e:
            print(f"[multisource] snapshot failed for {sport}: {e}")
            return {
                "live_by_id": {},
                "source": "snapshot",
                "error": str(e),
            }


def test_multisource():
    """Test the multisource aggregator"""
    from datetime import datetime
    
    today = datetime.now().isoformat()[:10]
    
    # Phase 1: Alternatives
    alt_sports = ["basketball", "hockey", "handball", "volleyball", "afl"]
    print("=== PHASE 1: Alternatives ===")
    for sport in alt_sports:
        result = LiveEventsMultiSource.get_live_events(sport, today)
        print(f"{sport}: source={result['source']}, count={result.get('count', 0)}")
        if result.get("error"):
            print(f"  └─ Error: {result['error']}")
    
    # Phase 2: ESPN
    espn_sports = ["football", "rugby", "american-football"]
    print("\n=== PHASE 2: ESPN ===")
    for sport in espn_sports:
        result = LiveEventsMultiSource.get_live_events(sport, today)
        print(f"{sport}: source={result['source']}, count={result.get('count', 0)}")
        if result.get("error"):
            print(f"  └─ Error: {result['error']}")
    
    # Fallback
    fallback_sports = ["tennis", "baseball", "mma"]
    print("\n=== FALLBACK: Snapshots ===")
    for sport in fallback_sports:
        result = LiveEventsMultiSource.get_live_events(sport, today)
        print(f"{sport}: source={result['source']}, count={result.get('count', 0)}")
        if result.get("error"):
            print(f"  └─ Error: {result['error']}")


if __name__ == "__main__":
    test_multisource()
