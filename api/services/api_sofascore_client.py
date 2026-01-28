"""
Simple Odds Estimator - Free alternative to betting odds APIs
Instead of fetching odds from external APIs, we estimate odds based on:
1. Live data from ESPN/alternatives (free, no auth)
2. Simple probability models
3. Historical patterns from event data

This approach is 100% FREE and requires no API authentication or rate limits
"""
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleOddsEstimator:
    """Generate estimated odds based on available data (completely free)"""
    
    # Default odds for different markets (if no better data available)
    DEFAULT_ODDS = {
        "home": 2.0,
        "away": 2.5,
        "draw": 3.2,
        "over": 1.95,
        "under": 1.95,
    }
    
    @staticmethod
    def estimate_odds_from_live_data(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate odds from live data (score, time, team strength)
        Completely deterministic, no API calls needed
        """
        home_score = event.get("homeScore")
        away_score = event.get("awayScore")
        status = event.get("status", "").lower()
        
        odds = SimpleOddsEstimator.DEFAULT_ODDS.copy()
        
        # Adjust odds based on current score
        if home_score is not None and away_score is not None:
            # Simple score-based adjustment
            diff = home_score - away_score
            
            if diff > 0:
                # Home is winning, lower home odds, higher away odds
                odds["home"] = max(1.1, odds["home"] - (0.2 * diff))
                odds["away"] = min(10.0, odds["away"] + (0.3 * diff))
            elif diff < 0:
                # Away is winning
                odds["away"] = max(1.1, odds["away"] - (0.2 * abs(diff)))
                odds["home"] = min(10.0, odds["home"] + (0.3 * abs(diff)))
            
            # Update draw odds
            if diff == 0:
                odds["draw"] = max(1.5, odds["draw"] - 0.5)
            else:
                odds["draw"] = min(4.0, odds["draw"] + 0.5)
        
        return odds
    
    @staticmethod
    def get_default_odds(sport: str, market: str = "1x2") -> Dict[str, float]:
        """Get default odds for a market"""
        if market in ["1x2", "moneyline", "home_away"]:
            return {
                "home": 1.9,
                "away": 2.0,
                "draw": 3.5,
            }
        elif market in ["over_under", "total"]:
            return {
                "over": 1.9,
                "under": 1.9,
            }
        return SimpleOddsEstimator.DEFAULT_ODDS


class SofaScoreClient:
    """
    Legacy wrapper (kept for compatibility)
    Now uses SimpleOddsEstimator instead of actual SofaScore API
    
    All operations are 100% free with no external API calls
    """
    
    BASE_URL = "https://api.sofascore.com/api/v1"
    
    SPORT_IDS = {
        "soccer": 17,
        "rugby": 84,
        "nfl": 115,
        "basketball": 18,
        "hockey": 80,
        "handball": 5,
        "volleyball": 1,
        "afl": 91,
        "tennis": 6,
        "baseball": 3,
        "f1": 25,
        "mma": 86,
    }
    
    def __init__(self):
        pass
    
    def get_events_with_odds(self, sport: str, date: str) -> Dict[str, Any]:
        """
        Get events with estimated odds (no API calls, completely free)
        date format: "YYYY-MM-DD"
        Returns: {sport, date, events: [{eventId, home, away, startTime, odds}]}
        """
        return {
            "sport": sport,
            "date": date,
            "events": [],
            "source": "simple_estimator",
            "count": 0,
            "note": "Use odds_estimation_multisport.py in pipeline instead"
        }
    
    def get_live_odds(self, sport: str) -> Dict[str, Any]:
        """Get live odds estimate (no API needed)"""
        return {
            "sport": sport,
            "events": [],
            "source": "simple_estimator",
            "count": 0,
        }

