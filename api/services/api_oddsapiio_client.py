"""
Odds-API.io Client - Real betting odds for 34+ sports (v3 API)
FREE tier: 100 requests/hour (or 500 requests/month)
Strategy: Fetch events list, then get odds for batches of up to 10 events
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
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class OddsAPIIOClient:
    """Client for Odds-API.io v3 with daily caching"""
    
    BASE_URL = "https://api.odds-api.io/v3"
    
    # Sport slug mappings (use exact slugs from /sports endpoint)
    SPORT_SLUGS = {
        # Solo deportes principales para no agotar quota
        "soccer": "football",
        "football": "football",
        "nfl": "american-football",
        "american-football": "american-football",
        "basketball": "basketball",
        "nba": "basketball",
        "hockey": "ice-hockey",
        "ice-hockey": "ice-hockey",
        "baseball": "baseball",
        "mlb": "baseball",
        "tennis": "tennis",
    }
    
    # Bookmakers available in FREE tier
    BOOKMAKERS = ["Bet365", "Unibet"]
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.api_key = os.environ.get("ODDS_APIIO_KEY")
        if not self.api_key:
            logger.warning("ODDS_APIIO_KEY not set in environment")
        
        self.session = requests.Session()
        
        # No retries - fail fast on errors
        retry_strategy = Retry(
            total=0,  # No retries
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.last_request_time = 0
        self.min_request_interval = 1.5  # 1.5 seconds between requests (rate limiting: 100 req/hr)

    def fetch_all_odds(self, day: str, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch odds for all sports.
        OPTIMIZED: 1 request per sport for events, then batch odds fetching (max 10 per request)
        Pipeline handles caching via /api/data/odds/{day}/ directory
        Returns: {sport: [events]}
        """
        
        if not self.api_key:
            logger.error("ODDS_APIIO_KEY not set in environment")
            return {}
        
        logger.info(f"Fetching odds for {day}")
        logger.info(f"Strategy: 1 request per sport + batch odds fetching (max 10 events/request)")
        
        # Step 1: Fetch events for ALL sports (18 requests maximum)
        logger.info(f"Step 1: Fetching events from {len(self.SPORT_SLUGS)} sports...")
        all_events_by_sport = {}
        
        for sport, sport_slug in self.SPORT_SLUGS.items():
            try:
                events = self._fetch_events_for_sport(sport, sport_slug)
                if events:
                    all_events_by_sport[sport] = events
                    logger.info(f"  {sport}: {len(events)} events (pending/live)")
            except Exception as e:
                logger.error(f"  {sport}: {str(e)}")
        
        # Step 2: Batch fetch odds for all events together (2-3 requests for ~30-50 events)
        logger.info(f"Step 2: Fetching odds in batches (max 10 events per request)...")
        
        all_odds = {}
        if all_events_by_sport:
            all_odds = self._fetch_odds_batch(all_events_by_sport)
        
        logger.info(f"Total: {sum(len(v) for v in all_odds.values())} events with odds")
        return all_odds
    
    def _fetch_events_for_sport(self, sport: str, sport_slug: str) -> List[Dict[str, Any]]:
        """Fetch all non-settled events for a specific sport (1 request)"""
        
        try:
            # Rate limiting
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
            
            events_url = f"{self.BASE_URL}/events"
            params = {
                "apiKey": self.api_key,
                "sport": sport_slug,
            }
            
            response = self.session.get(events_url, params=params, timeout=10)
            self.last_request_time = time.time()
            
            if response.status_code != 200:
                logger.debug(f"HTTP {response.status_code} for {sport}")
                return []
            
            all_events = response.json()
            
            # Filter for non-settled events only
            pending_events = [e for e in all_events if e.get('status') != 'settled']
            
            return pending_events
        
        except Exception as e:
            logger.error(f"Error fetching events for {sport}: {str(e)}")
            return []
    
    def _fetch_odds_batch(self, all_events_by_sport: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch odds for all events in batches of max 10 (optimized: few requests)"""
        
        # Accumulate all events with their sport
        all_events_with_sport = []
        for sport, events in all_events_by_sport.items():
            for event in events:
                all_events_with_sport.append((sport, event))
        
        logger.info(f"Total events to fetch odds for: {len(all_events_with_sport)}")
        
        all_odds = {}
        batch_size = 10  # Max per /v3/odds/multi request
        
        for i in range(0, len(all_events_with_sport), batch_size):
            batch = all_events_with_sport[i:i+batch_size]
            event_ids = ",".join(str(event['id']) for _, event in batch)
            
            # Rate limiting between batches
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
            
            try:
                odds_url = f"{self.BASE_URL}/odds/multi"
                odds_params = {
                    "apiKey": self.api_key,
                    "eventIds": event_ids,
                    "bookmakers": ",".join(self.BOOKMAKERS),
                }
                
                batch_num = (i // batch_size) + 1
                total_batches = (len(all_events_with_sport) + batch_size - 1) // batch_size
                logger.debug(f"Batch {batch_num}/{total_batches}: Fetching odds for {len(batch)} events")
                
                response = self.session.get(odds_url, params=odds_params, timeout=10)
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    odds_events = response.json()
                    
                    for odds_event in odds_events:
                        # Find which sport this event belongs to
                        sport_for_event = None
                        for sport, event in batch:
                            if event['id'] == odds_event.get('id'):
                                sport_for_event = sport
                                break
                        
                        if sport_for_event:
                            normalized = self._normalize_event(odds_event, sport_for_event)
                            if normalized:
                                if sport_for_event not in all_odds:
                                    all_odds[sport_for_event] = []
                                all_odds[sport_for_event].append(normalized)
                else:
                    logger.warning(f"HTTP {response.status_code} fetching odds batch {batch_num}")
            
            except Exception as e:
                logger.error(f"Error fetching odds batch {batch_num}: {str(e)}")
        
        return all_odds
    
    def _normalize_event(self, event: Dict[str, Any], sport: str) -> Optional[Dict[str, Any]]:
        """Normalize Odds-API.io event format to our internal format
        
        Extracts ALL markets available: h2h, spreads, totals
        Returns normalized event with all market data preserved
        """
        
        try:
            event_id = event.get("id")
            home_team = event.get("home", "")
            away_team = event.get("away", "")
            start_time = event.get("date", "")
            
            if not event_id or not home_team or not away_team:
                return None
            
            # Extract ALL odds/markets from bookmakers
            # Odds-API.io v3 returns: bookmakers: {Bet365: [{name, price, market?, point?}]}
            all_markets = {}  # {market_name: {outcome: price, point?}}
            bookmakers = event.get("bookmakers", {})
            
            if isinstance(bookmakers, dict):
                for bookmaker_name in self.BOOKMAKERS:
                    bm_outcomes = bookmakers.get(bookmaker_name, [])
                    
                    # bm_outcomes is a list with outcomes from all markets
                    for outcome in bm_outcomes:
                        price = outcome.get("price")
                        name = outcome.get("name", "")
                        market = outcome.get("market", "h2h")  # Default to h2h if not specified
                        point = outcome.get("point")
                        
                        if not price or not name:
                            continue
                        
                        if market not in all_markets:
                            all_markets[market] = {}
                        
                        # Store outcome with best (highest) odds
                        outcome_key = f"{name}|{point}" if point else name
                        if outcome_key not in all_markets[market] or price > all_markets[market][outcome_key].get("price", 0):
                            all_markets[market][outcome_key] = {
                                "price": price,
                                "name": name,
                                "point": point
                            }
            
            # Only include if we have at least h2h home odds
            if not all_markets.get("h2h", {}).get(home_team):
                return None
            
            return {
                "eventId": event_id,
                "sport": sport,
                "home": home_team,
                "away": away_team,
                "markets": all_markets,  # All markets: h2h, spreads, totals, etc
                "startTime": start_time,
                "odds": {
                    "home": odds_dict.get("home"),
                    "away": odds_dict.get("away"),
                },
                "source": "odds_apiio"
            }
        
        except Exception as e:
            logger.debug(f"Error normalizing event: {e}")
            return None


if __name__ == "__main__":
    import sys
    
    # Test
    client = OddsAPIIOClient()
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    
    result = client.fetch_all_odds(day, force_refresh=True)
    print(json.dumps({
        "day": day,
        "sports_fetched": list(result.keys()),
        "total_events": sum(len(v) for v in result.values()),
    }, indent=2))
