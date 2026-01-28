"""
The Odds API Client with Daily Caching - Real betting odds for 9 sports
FREE tier: 500 requests/month (~17 requests/day available)
Strategy: Fetch all odds ONCE per day (at 6am), cache results, reuse throughout day
"""
import requests
from typing import Dict, List, Any, Optional
import logging
import os
import json
from pathlib import Path
import time
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class TheOddsAPICached:
    """Client for The Odds API with daily caching to reduce quota consumption"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Sport ID mappings in The Odds API
    SPORT_TO_ODDS_ID = {
        "soccer": "soccer_epl",
        "football": "soccer_epl",
        "rugby": "rugby_union",
        "nfl": "americanfootball_nfl",
        "basketball": "basketball_nba",
        "hockey": "icehockey_nhl",
        "afl": "aussierules_afl",
        "tennis": "tennis_atp",
        "baseball": "baseball_mlb",
        "f1": "mma_ufc",
    }
    
    BOOKMAKERS = [
        "draftkings",
        "fanduel",
        "betmgm",
        "betrivers",
    ]
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.api_key = os.environ.get("ODDS_API_KEY")
        if not self.api_key:
            logger.warning("ODDS_API_KEY not set in environment")
        
        self.session = requests.Session()
        
        # Add retry strategy for rate limits
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 seconds between requests
        
        # Cache directory
        if cache_dir is None:
            repo_root = Path(__file__).resolve().parents[2]
            cache_dir = repo_root / "api" / "data" / ".odds_cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cached_path(self, day: str) -> Path:
        """Get path to cached odds file for a specific day"""
        return self.cache_dir / f"{day}_odds.json"
    
    def is_cache_fresh(self, day: str, max_age_hours: int = 6) -> bool:
        """Check if cache exists and is fresh"""
        cache_file = self.get_cached_path(day)
        if not cache_file.exists():
            return False
        
        file_age = time.time() - cache_file.stat().st_mtime
        max_age_seconds = max_age_hours * 3600
        return file_age < max_age_seconds
    
    def load_from_cache(self, day: str) -> Optional[Dict[str, Any]]:
        """Load odds from cache file"""
        cache_file = self.get_cached_path(day)
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache from {cache_file}: {e}")
            return None
    
    def save_to_cache(self, day: str, data: Dict[str, Any]) -> None:
        """Save odds to cache file"""
        cache_file = self.get_cached_path(day)
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cached odds for {day} at {cache_file}")
        except Exception as e:
            logger.error(f"Error saving cache to {cache_file}: {e}")
    
    def fetch_all_odds(self, day: str, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch odds for all sports, using cache when available.
        Returns: {sport: [events]}
        """
        
        # Try cache first (unless force_refresh)
        if not force_refresh and self.is_cache_fresh(day, max_age_hours=6):
            logger.info(f"Using cached odds for {day}")
            cached = self.load_from_cache(day)
            if cached:
                return cached
        
        if not self.api_key:
            logger.warning("ODDS_API_KEY not configured, attempting to use cache")
            cached = self.load_from_cache(day)
            return cached if cached else {}
        
        logger.info(f"Fetching fresh odds for {day} (using {len(self.SPORT_TO_ODDS_ID)} sports)")
        
        all_odds = {}
        errors = []
        
        for sport in self.SPORT_TO_ODDS_ID.keys():
            result = self.get_events_with_odds(sport, day)
            events = result.get("events", [])
            
            if events:
                all_odds[sport] = events
                logger.info(f"  {sport}: {len(events)} events")
            else:
                error = result.get("error")
                if error:
                    errors.append(f"{sport}: {error}")
                    logger.warning(f"  {sport}: {error}")
        
        # Save to cache even if some sports failed
        cache_data = {
            "day": day,
            "fetched_at": datetime.now().isoformat(),
            "sports": all_odds,
            "errors": errors,
        }
        self.save_to_cache(day, cache_data)
        
        return all_odds
    
    def get_events_with_odds(self, sport: str, day: Optional[str] = None) -> Dict[str, Any]:
        """
        Get events with real betting odds for a sport
        Returns: {sport, events: [...]}
        """
        if not self.api_key:
            return {"sport": sport, "events": [], "error": "ODDS_API_KEY not configured"}
        
        sport_lower = sport.lower()
        odds_sport_id = self.SPORT_TO_ODDS_ID.get(sport_lower)
        
        if not odds_sport_id:
            return {"sport": sport, "events": [], "error": f"Sport {sport} not supported"}
        
        try:
            # Rate limit: ensure minimum interval between requests
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
            
            url = f"{self.BASE_URL}/sports/{odds_sport_id}/events"
            params = {
                "apiKey": self.api_key,
                "markets": "h2h",
            }
            
            response = self.session.get(url, params=params, timeout=10)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            data = response.json()
            
            events = data.get("data", []) if isinstance(data, dict) else []
            
            # Normalize events
            normalized_events = []
            for event in events[:50]:
                try:
                    normalized = self._normalize_event(event, sport)
                    if normalized:
                        normalized_events.append(normalized)
                except Exception as e:
                    logger.debug(f"Error normalizing event: {e}")
                    continue
            
            return {
                "sport": sport,
                "events": normalized_events,
                "source": "theodds_api",
                "count": len(normalized_events),
            }
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"TheOddsAPI rate limit (429) for {sport}")
                return {"sport": sport, "events": [], "error": "Rate limit exceeded"}
            else:
                logger.error(f"TheOddsAPI HTTP error for {sport}: {e}")
                return {"sport": sport, "events": [], "error": str(e)}
        except Exception as e:
            logger.error(f"TheOddsAPI error for {sport}: {e}")
            return {"sport": sport, "events": [], "error": str(e)}
    
    def _normalize_event(self, event: Dict[str, Any], sport: str) -> Optional[Dict[str, Any]]:
        """Normalize event data from The Odds API"""
        try:
            event_id = event.get("id")
            home_team = event.get("home_team")
            away_team = event.get("away_team")
            commence_time = event.get("commence_time")
            
            if not (event_id and home_team and away_team):
                return None
            
            odds_by_market = {}
            bookmakers = event.get("bookmakers", [])
            
            for bookmaker in bookmakers:
                bookie_name = bookmaker.get("key")
                markets = bookmaker.get("markets", [])
                
                for market in markets:
                    market_key = market.get("key")
                    outcomes = market.get("outcomes", [])
                    
                    if market_key == "h2h" and len(outcomes) >= 2:
                        if not odds_by_market.get("h2h"):
                            odds_by_market["h2h"] = {}
                        
                        odds_by_market["h2h"][bookie_name] = {
                            "home": float(outcomes[0].get("price", 0)),
                            "away": float(outcomes[1].get("price", 0)),
                        }
            
            best_odds = self._get_best_odds(odds_by_market)
            
            normalized = {
                "eventId": str(event_id),
                "sport": sport,
                "home": home_team,
                "away": away_team,
                "startTime": commence_time,
                "odds": best_odds,
                "source": "theodds_api",
            }
            
            return normalized
        
        except Exception as e:
            logger.debug(f"Error normalizing event: {e}")
            return None
    
    def _get_best_odds(self, odds_by_market: Dict[str, Any]) -> Dict[str, float]:
        """Extract best (highest) odds from all bookmakers"""
        best = {}
        
        h2h_odds = odds_by_market.get("h2h", {})
        
        if h2h_odds:
            home_odds = []
            away_odds = []
            
            for bookie_data in h2h_odds.values():
                home_odds.append(bookie_data.get("home", 0))
                away_odds.append(bookie_data.get("away", 0))
            
            if home_odds:
                best["home"] = max(home_odds)
            if away_odds:
                best["away"] = max(away_odds)
        
        return best
