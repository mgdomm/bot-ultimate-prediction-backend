"""
SportsGameOdds.com Client - 8 Sports, 9 Bookmakers, FREE tier
Strategy: 1 request per day per sport (8 requests/day max)
"""
import os

# Load .env before anything else
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests
from typing import Dict, List, Any, Optional
import logging
import json
from pathlib import Path
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class SportsGameOddsClient:
    """Client for SportsGameOdds.com v2 API with daily caching (FREE tier, 2,500 objects/month)"""
    
    BASE_URL = "https://api.sportsgameodds.com/v2"
    
    # 8 deportes soportados en tier FREE
    SPORTS_CONFIG = {
        "nfl": "NFL",
        "nba": "NBA",
        "mlb": "MLB",
        "nhl": "NHL",
        "college_football": "NCAAF",
        "college_basketball": "NCAAB",
        "soccer_champions": "UEFA_CHAMPIONS_LEAGUE",
        "soccer_mls": "MLS",
    }
    
    # 9 bookmakers disponibles
    BOOKMAKERS = [
        "fanduel",
        "draftkings",
        "betmgm",
        "caesars",
        "espnbet",
        "bovada",
        "unibet",
        "pointsbet",
        "williamhill",
    ]
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.api_key = os.environ.get("SPORTS_GAME_ODDS_API_KEY")
        if not self.api_key:
            logger.warning("SPORTS_GAME_ODDS_API_KEY not set in environment")
        
        self.session = requests.Session()
        
        # NO retries - fail fast on errors (respect quota)
        retry_strategy = Retry(
            total=0,  # No retries
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.last_request_time = 0
        self.min_request_interval = 6.0  # SportsGameOdds limit: 10 req/minute = 1 req per 6 seconds
        
        # Cache dir: /api/data/odds_sportsgameodds/{day}/
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            repo_root = Path(__file__).resolve().parents[2]
            self.cache_dir = repo_root / "api" / "data" / "odds_sportsgameodds"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_file(self, day: str, league_id: str) -> Path:
        """Cache file for specific league/day"""
        return self.cache_dir / day / f"{league_id}.json"
    
    def _load_cache(self, day: str, league_id: str) -> Optional[List[Dict[str, Any]]]:
        """Load cached events for a league"""
        cache_file = self._get_cache_file(day, league_id)
        if not cache_file.exists():
            return None
        
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "data" in data:
                return data["data"]
        except Exception as e:
            logger.warning(f"Error loading cache for {league_id}/{day}: {e}")
        
        return None
    
    def _save_cache(self, day: str, league_id: str, events: List[Dict[str, Any]]) -> None:
        """Save events to cache"""
        cache_file = self._get_cache_file(day, league_id)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            cache_file.write_text(json.dumps(events), encoding="utf-8")
        except Exception as e:
            logger.error(f"Error saving cache for {league_id}/{day}: {e}")
    
    def _rate_limit(self) -> None:
        """Simple rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
    
    def _fetch_events_for_league(self, day: str, league_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch RAW events for a specific league (1 API request)
        Returns: List of RAW event dicts from API (not normalized)
        """
        
        # Try cache first (unless force_refresh)
        if not force_refresh:
            cached = self._load_cache(day, league_id)
            if cached is not None:
                logger.debug(f"Using cached events for {league_id} ({len(cached)} events)")
                return cached
        
        if not self.api_key:
            logger.error("SPORTS_GAME_ODDS_API_KEY not set, skipping API call")
            return []
        
        try:
            self._rate_limit()
            
            # Main endpoint: /events with league filter
            url = f"{self.BASE_URL}/events"
            params = {
                "leagueID": league_id,
                "oddsAvailable": "true",  # Only events with active odds
                "limit": 50,  # Max per request
                "bookmakerID": ",".join(self.BOOKMAKERS),  # Filter to our bookmakers
                "x-api-key": self.api_key,  # Auth in query param (alternative to header)
            }
            
            headers = {
                "x-api-key": self.api_key,  # Auth in header (preferred)
            }
            
            logger.debug(f"Fetching events for {league_id}")
            response = self.session.get(url, params=params, headers=headers, timeout=15)
            self.last_request_time = time.time()
            
            if response.status_code == 401:
                logger.error(f"Unauthorized (401) - check SPORTS_GAME_ODDS_API_KEY")
                return []
            
            if response.status_code == 429:
                logger.error(f"Rate limited (429) - quota exceeded for {league_id}")
                return []
            
            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} fetching {league_id}: {response.text[:200]}")
                return []
            
            data = response.json()
            
            # Response format: {"success": true, "data": [...], "nextCursor": "..."}
            if not data.get("success"):
                error = data.get("error", "Unknown error")
                logger.warning(f"API error for {league_id}: {error}")
                return []
            
            events = data.get("data", [])
            logger.info(f"Fetched {len(events)} events for {league_id}")
            
            # Save to cache for next 24 hours
            self._save_cache(day, league_id, events)
            
            return events
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {league_id}")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error fetching {league_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching events for {league_id}: {e}")
            return []
    
    def fetch_all_odds(self, day: str, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch RAW odds data for all sports (up to 8 API requests, one per league)
        
        Returns: {sport: [raw_events]}
        
        NOTE: Events are RAW from API, not normalized. Normalization happens in odds_ingestion_multisport.py
        """
        
        if not self.api_key:
            logger.error("SPORTS_GAME_ODDS_API_KEY not set")
            return {}
        
        logger.info(f"SportsGameOdds: Fetching RAW odds for {day}")
        logger.info(f"Strategy: 1 request per sport (max 8/day), cached by day")
        
        all_odds = {}
        
        for sport, league_id in self.SPORTS_CONFIG.items():
            try:
                events = self._fetch_events_for_league(day, league_id, force_refresh)
                
                if events:
                    # Store RAW events indexed by sport name (not league_id)
                    # odds_ingestion_multisport.py will handle normalization
                    all_odds[sport] = events
                    logger.info(f"  {sport}: {len(events)} raw events")
                else:
                    all_odds[sport] = []
                    logger.debug(f"  {sport}: 0 events")
            
            except Exception as e:
                logger.error(f"  {sport}: Unexpected error: {e}")
                all_odds[sport] = []
        
        logger.info(f"Total: {sum(len(v) for v in all_odds.values())} raw events fetched")
        return all_odds
    
    def _normalize_event(self, event: Dict[str, Any], sport: str) -> Optional[Dict[str, Any]]:
        """
        Normalize SportsGameOdds event to internal format
        
        SportsGameOdds structure:
        {
          "eventID": "...",
          "status": {"oddsAvailable": true, "started": false, ...},
          "teams": {"home": {...}, "away": {...}},
          "odds": {
            "points-home-reg-ml-home": {
              "fairOdds": "+110",
              "bookOdds": "+115",
              "byBookmaker": {
                "fanduel": {"odds": "+115"},
                ...
              }
            }
          }
        }
        """
        
        try:
            event_id = event.get("eventID")
            if not event_id:
                return None
            
            # Skip if not open for betting
            status = event.get("status", {})
            if not status.get("oddsAvailable"):
                return None
            
            if status.get("started") or status.get("live") or status.get("ended") or status.get("cancelled"):
                return None
            
            teams = event.get("teams", {})
            home_team = teams.get("home", {}).get("names", {}).get("short", "HOME")
            away_team = teams.get("away", {}).get("names", {}).get("short", "AWAY")
            
            # Extract odds markets
            all_markets = {}
            odds_data = event.get("odds", {})
            
            if not odds_data:
                return None
            
            # Collect all markets (h2h, spreads, ou, etc)
            for odd_id, odd_info in odds_data.items():
                if not odd_info.get("bookOddsAvailable") and not odd_info.get("fairOddsAvailable"):
                    continue
                
                # Extract market type from oddID: points-home-reg-ml-home
                parts = odd_id.split("-")
                if len(parts) < 5:
                    continue
                
                market_name = parts[2]  # "reg", "1h", "game"
                bet_type = parts[3]     # "ml", "sp", "ou"
                side = parts[4]         # "home", "away", "over", "under"
                
                market_key = f"{bet_type}_{market_name}"
                if market_key not in all_markets:
                    all_markets[market_key] = []
                
                # Extract odds from bookmakers
                by_bookmaker = odd_info.get("byBookmaker", {})
                
                for bm_id, bm_odds in by_bookmaker.items():
                    odds_value = bm_odds.get("odds")
                    if odds_value:
                        all_markets[market_key].append({
                            "bookmaker": bm_id,
                            "side": side,
                            "odds": odds_value,
                            "point": odd_info.get("bookSpread") or odd_info.get("fairSpread"),
                        })
            
            if not all_markets:
                return None
            
            start_time = status.get("startsAt", "")
            
            return {
                "eventId": event_id,
                "sport": sport,
                "home": home_team,
                "away": away_team,
                "markets": all_markets,
                "startTime": start_time,
                "odds": {
                    "home": None,  # Could extract from markets
                    "away": None,
                },
                "source": "sportsgameodds"
            }
        
        except Exception as e:
            logger.debug(f"Error normalizing event: {e}")
            return None


if __name__ == "__main__":
    import sys
    
    # Test
    client = SportsGameOddsClient()
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    
    result = client.fetch_all_odds(day, force_refresh=False)
    print(json.dumps({
        "day": day,
        "sports_fetched": list(result.keys()),
        "total_events": sum(len(v) for v in result.values()),
        "details": {sport: len(events) for sport, events in result.items()}
    }, indent=2))
