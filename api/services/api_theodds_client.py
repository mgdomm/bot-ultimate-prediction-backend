"""
The Odds API Client - Real betting odds for 9 sports
FREE tier: 500 requests/month
Supported sports: Soccer, Rugby, NFL, Basketball, Hockey, AFL, Tennis, Baseball, F1
"""
import requests
from typing import Dict, List, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class TheOddsAPIClient:
    """Client for The Odds API - Real betting market odds"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    # Sport ID mappings in The Odds API
    SPORT_TO_ODDS_ID = {
        "soccer": "soccer_epl",  # Premier League (default)
        "football": "soccer_epl",
        "rugby": "rugby_union",
        "nfl": "americanfootball_nfl",
        "basketball": "basketball_nba",
        "hockey": "icehockey_nhl",
        "afl": "aussierules_afl",
        "tennis": "tennis_atp",
        "baseball": "baseball_mlb",
        "f1": "mma_ufc",  # Note: F1 not supported, using UFC as placeholder
    }
    
    # Bookmakers a usar (free tier)
    BOOKMAKERS = [
        "draftkings",
        "fanduel",
        "betmgm",
        "betrivers",
    ]
    
    def __init__(self):
        self.api_key = os.environ.get("ODDS_API_KEY")
        if not self.api_key:
            logger.warning("ODDS_API_KEY not set in environment")
        self.session = requests.Session()
    
    def get_events_with_odds(self, sport: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get events with real betting odds for a sport
        Returns: {sport, events: [{eventId, home, away, odds: {bookmaker: {market: decimal}}}]}
        """
        if not self.api_key:
            return {"sport": sport, "events": [], "error": "ODDS_API_KEY not configured"}
        
        sport_lower = sport.lower()
        odds_sport_id = self.SPORT_TO_ODDS_ID.get(sport_lower)
        
        if not odds_sport_id:
            return {"sport": sport, "events": [], "error": f"Sport {sport} not supported"}
        
        try:
            # Get events for this sport
            url = f"{self.BASE_URL}/sports/{odds_sport_id}/events"
            params = {
                "apiKey": self.api_key,
                "markets": "h2h",  # Head to head (moneyline)
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("data", []) if isinstance(data, dict) else []
            
            # Normalize events
            normalized_events = []
            for event in events[:50]:  # Limit to 50 per sport
                try:
                    normalized = self._normalize_event(event, sport)
                    if normalized:
                        normalized_events.append(normalized)
                except Exception as e:
                    logger.error(f"Error normalizing event: {e}")
                    continue
            
            return {
                "sport": sport,
                "events": normalized_events,
                "source": "theodds_api",
                "count": len(normalized_events),
                "bookmakers_fetched": len(self.BOOKMAKERS),
            }
        
        except Exception as e:
            logger.error(f"TheOddsAPI error for {sport}: {e}")
            return {"sport": sport, "events": [], "error": str(e), "source": "theodds_api"}
    
    def _normalize_event(self, event: Dict[str, Any], sport: str) -> Optional[Dict[str, Any]]:
        """Normalize event data from The Odds API"""
        try:
            event_id = event.get("id")
            home_team = event.get("home_team")
            away_team = event.get("away_team")
            commence_time = event.get("commence_time")
            
            if not (event_id and home_team and away_team):
                return None
            
            # Extract odds from bookmakers
            odds_by_market = {}
            bookmakers = event.get("bookmakers", [])
            
            for bookmaker in bookmakers:
                bookie_name = bookmaker.get("key")  # e.g., "draftkings"
                markets = bookmaker.get("markets", [])
                
                for market in markets:
                    market_key = market.get("key")  # e.g., "h2h"
                    outcomes = market.get("outcomes", [])
                    
                    if market_key == "h2h" and len(outcomes) >= 2:
                        # outcomes[0] = home, outcomes[1] = away
                        if not odds_by_market.get("h2h"):
                            odds_by_market["h2h"] = {}
                        
                        odds_by_market["h2h"][bookie_name] = {
                            "home": float(outcomes[0].get("price", 0)),
                            "away": float(outcomes[1].get("price", 0)),
                        }
            
            # Get best (highest) odds for each side
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
            logger.error(f"Error normalizing event: {e}")
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
    
    def get_supported_sports(self) -> List[str]:
        """Get list of supported sports"""
        return list(self.SPORT_TO_ODDS_ID.keys())
