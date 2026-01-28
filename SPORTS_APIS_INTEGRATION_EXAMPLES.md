# Integration Examples for bot-ultimate-prediction-backend

## Overview
This file shows how to integrate the recommended APIs directly into your backend structure.

---

## 1. MLB Stats Service Integration

### File: `api/services/mlb_stats_service.py`

```python
"""
MLB Stats Service
Provides real-time MLB game data, scores, and statistics
Source: https://statsapi.mlb.com/api/v1/
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from api.services.safe_call import safe_call

logger = logging.getLogger(__name__)

class MLBStatsService:
    """Service for fetching MLB statistics and live game data"""
    
    BASE_URL = "https://statsapi.mlb.com/api/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'bot-ultimate-prediction/1.0'
        })
    
    @safe_call
    def get_schedule(self, date_str: str = None) -> List[Dict]:
        """
        Get MLB schedule for a specific date
        
        Args:
            date_str: Date in format 'YYYY-MM-DD' (defaults to today)
            
        Returns:
            List of game dictionaries
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.BASE_URL}/schedule"
        params = {'date': date_str}
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date_str}")
        
        return games
    
    @safe_call
    def get_live_game(self, game_id: int) -> Dict:
        """
        Get detailed live game data
        
        Args:
            game_id: MLB game ID (gamePk)
            
        Returns:
            Game data dictionary
        """
        url = f"{self.BASE_URL}/game/{game_id}/linescore"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    @safe_call
    def get_game_box_score(self, game_id: int) -> Dict:
        """Get detailed box score for a game"""
        url = f"{self.BASE_URL}/game/{game_id}/boxscore"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    @safe_call
    def get_player_stats(self, player_id: int) -> Dict:
        """Get statistics for a specific player"""
        url = f"{self.BASE_URL}/people/{player_id}"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    @safe_call
    def get_standings(self, season: int = None) -> List[Dict]:
        """Get current league standings"""
        if season is None:
            season = datetime.now().year
        
        url = f"{self.BASE_URL}/standings"
        params = {'leagueId': '103,104', 'season': season}
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json().get('records', [])
    
    def get_games_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get all games between two dates"""
        all_games = []
        
        current = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            games = self.get_schedule(date_str)
            all_games.extend(games)
            current += timedelta(days=1)
        
        return all_games


# Singleton instance
mlb_service = MLBStatsService()
```

### Usage in `api/main.py`
```python
from api.services.mlb_stats_service import mlb_service
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/mlb/schedule/{date}")
async def get_mlb_schedule(date: str):
    """Get MLB schedule for a specific date"""
    games = mlb_service.get_schedule(date)
    return {
        'date': date,
        'game_count': len(games),
        'games': games
    }

@router.get("/api/mlb/live/{game_id}")
async def get_mlb_live_game(game_id: int):
    """Get live game data"""
    data = mlb_service.get_live_game(game_id)
    return data

@router.get("/api/mlb/standings/{season}")
async def get_mlb_standings(season: int = None):
    """Get league standings"""
    standings = mlb_service.get_standings(season)
    return standings
```

---

## 2. Tennis Service Integration (ESPN)

### File: `api/services/tennis_service.py`

```python
"""
Tennis Service
Provides ATP/WTA match data from ESPN
Source: https://site.api.espn.com/us/site/v2/sports/tennis/
"""

import requests
import logging
from typing import List, Dict, Optional
from api.services.safe_call import safe_call

logger = logging.getLogger(__name__)

class TennisService:
    """Service for fetching tennis match data"""
    
    BASE_URL = "https://site.api.espn.com/us/site/v2/sports/tennis"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'bot-ultimate-prediction/1.0'
        })
    
    @safe_call
    def get_atp_matches(self) -> Dict:
        """Get current ATP matches"""
        url = f"{self.BASE_URL}/atp"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Retrieved {len(data.get('events', []))} ATP matches")
        
        return data
    
    @safe_call
    def get_wta_matches(self) -> Dict:
        """Get current WTA matches"""
        url = f"{self.BASE_URL}/wta"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Retrieved {len(data.get('events', []))} WTA matches")
        
        return data
    
    def extract_match_details(self, event: Dict) -> Dict:
        """Extract relevant match details from ESPN event"""
        competitors = event.get('competitors', [])
        
        match_data = {
            'id': event.get('id'),
            'tournament': event.get('tournament', {}).get('name', 'Unknown'),
            'status': event.get('status', 'Unknown'),
            'player1': {
                'name': competitors[0].get('displayName', 'Unknown') if len(competitors) > 0 else None,
                'seed': competitors[0].get('seed', 'NR') if len(competitors) > 0 else None,
                'score': competitors[0].get('score') if len(competitors) > 0 else None,
            } if len(competitors) > 0 else None,
            'player2': {
                'name': competitors[1].get('displayName', 'Unknown') if len(competitors) > 1 else None,
                'seed': competitors[1].get('seed', 'NR') if len(competitors) > 1 else None,
                'score': competitors[1].get('score') if len(competitors) > 1 else None,
            } if len(competitors) > 1 else None,
        }
        
        return match_data
    
    def get_active_matches(self, league: str = 'atp') -> List[Dict]:
        """Get list of active matches"""
        if league.lower() == 'atp':
            data = self.get_atp_matches()
        else:
            data = self.get_wta_matches()
        
        events = data.get('events', [])
        active = [e for e in events if e.get('status') in ['IN_PROGRESS', 'SCHEDULED']]
        
        return [self.extract_match_details(e) for e in active]


# Singleton instance
tennis_service = TennisService()
```

### Usage in `api/main.py`
```python
from api.services.tennis_service import tennis_service

@router.get("/api/tennis/atp/live")
async def get_atp_matches():
    """Get current ATP matches"""
    matches = tennis_service.get_active_matches('atp')
    return {
        'league': 'ATP',
        'match_count': len(matches),
        'matches': matches
    }

@router.get("/api/tennis/wta/live")
async def get_wta_matches():
    """Get current WTA matches"""
    matches = tennis_service.get_active_matches('wta')
    return {
        'league': 'WTA',
        'match_count': len(matches),
        'matches': matches
    }
```

---

## 3. Odds API Integration

### File: `api/services/odds_service.py`

```python
"""
Odds Service
Provides betting odds from The Odds API
Source: https://api.the-odds-api.com/v4/
"""

import requests
import logging
import os
from typing import List, Dict, Optional
from api.services.safe_call import safe_call
from api.services.logger import logger

class OddsService:
    """Service for fetching sports betting odds"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ODDS_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'bot-ultimate-prediction/1.0'
        })
    
    @safe_call
    def get_sports(self) -> List[Dict]:
        """Get available sports"""
        url = f"{self.BASE_URL}/sports"
        params = {'api_key': self.api_key}
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    @safe_call
    def get_odds(self, sport: str, regions: str = 'us', markets: str = 'h2h') -> List[Dict]:
        """
        Get betting odds for a specific sport
        
        Args:
            sport: Sport key (e.g., 'baseball_mlb', 'tennis_atp', 'tennis_wta')
            regions: Comma-separated regions (e.g., 'us', 'uk', 'au')
            markets: Comma-separated markets (e.g., 'h2h', 'spreads', 'totals')
            
        Returns:
            List of games with odds
        """
        url = f"{self.BASE_URL}/sports/{sport}/odds"
        params = {
            'api_key': self.api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': 'decimal'
        }
        
        response = self.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Retrieved odds for {len(data)} games in {sport}")
        
        return data
    
    def get_best_odds(self, sport: str) -> Dict:
        """Find best odds across all bookmakers for a sport"""
        odds_data = self.get_odds(sport)
        
        best_odds = {}
        for game in odds_data:
            game_key = f"{game.get('away_team', 'N/A')} @ {game.get('home_team', 'N/A')}"
            best_odds[game_key] = {
                'away': {'price': 0, 'bookmaker': 'N/A'},
                'home': {'price': 0, 'bookmaker': 'N/A'}
            }
            
            for bookmaker in game.get('bookmakers', []):
                title = bookmaker.get('title', 'N/A')
                
                for market in bookmaker.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        price = outcome.get('price', 0)
                        name = outcome.get('name', '')
                        
                        if name == game.get('away_team'):
                            if price > best_odds[game_key]['away']['price']:
                                best_odds[game_key]['away'] = {
                                    'price': price,
                                    'bookmaker': title
                                }
                        elif name == game.get('home_team'):
                            if price > best_odds[game_key]['home']['price']:
                                best_odds[game_key]['home'] = {
                                    'price': price,
                                    'bookmaker': title
                                }
        
        return best_odds
    
    def get_mlb_odds(self) -> List[Dict]:
        """Get MLB betting odds"""
        return self.get_odds('baseball_mlb')
    
    def get_tennis_odds(self, league: str = 'atp') -> List[Dict]:
        """Get tennis odds (ATP or WTA)"""
        sport_key = f'tennis_{league.lower()}'
        return self.get_odds(sport_key)


# Singleton instance
odds_service = OddsService()
```

### Usage in `api/main.py`
```python
from api.services.odds_service import odds_service

@router.get("/api/odds/mlb")
async def get_mlb_odds():
    """Get MLB betting odds"""
    odds = odds_service.get_mlb_odds()
    best = odds_service.get_best_odds('baseball_mlb')
    
    return {
        'sport': 'MLB',
        'game_count': len(odds),
        'odds': odds,
        'best_odds': best
    }

@router.get("/api/odds/tennis/{league}")
async def get_tennis_odds(league: str = 'atp'):
    """Get tennis odds"""
    odds = odds_service.get_tennis_odds(league)
    
    return {
        'league': league.upper(),
        'match_count': len(odds),
        'odds': odds
    }
```

---

## 4. Unified Sports Feed Service

### File: `api/services/sports_feed_service.py`

```python
"""
Unified Sports Feed Service
Combines MLB, Tennis, and Odds data into a single feed
"""

import logging
from typing import Dict
from datetime import datetime
from api.services.mlb_stats_service import mlb_service
from api.services.tennis_service import tennis_service
from api.services.odds_service import odds_service

logger = logging.getLogger(__name__)

class SportsFeeder:
    """Unified service for all sports data"""
    
    def __init__(self):
        self.mlb = mlb_service
        self.tennis = tennis_service
        self.odds = odds_service
    
    def get_combined_feed(self, include_odds: bool = True) -> Dict:
        """Get combined feed of all sports data"""
        
        feed = {
            'timestamp': datetime.now().isoformat(),
            'mlb': {
                'schedule': self.mlb.get_schedule(),
                'odds': self.odds.get_mlb_odds() if include_odds else []
            },
            'tennis': {
                'atp': {
                    'matches': self.tennis.get_active_matches('atp'),
                    'odds': self.odds.get_tennis_odds('atp') if include_odds else []
                },
                'wta': {
                    'matches': self.tennis.get_active_matches('wta'),
                    'odds': self.odds.get_tennis_odds('wta') if include_odds else []
                }
            }
        }
        
        logger.info(f"Generated sports feed with {len(feed['mlb']['schedule'])} MLB games")
        
        return feed
    
    def get_mlb_feed(self, date: str = None, include_odds: bool = True) -> Dict:
        """Get MLB-specific feed"""
        schedule = self.mlb.get_schedule(date)
        odds = self.odds.get_mlb_odds() if include_odds else []
        
        return {
            'date': date or datetime.now().strftime('%Y-%m-%d'),
            'game_count': len(schedule),
            'games': schedule,
            'odds': odds
        }
    
    def get_tennis_feed(self, league: str = 'atp', include_odds: bool = True) -> Dict:
        """Get tennis-specific feed"""
        matches = self.tennis.get_active_matches(league)
        odds = self.odds.get_tennis_odds(league) if include_odds else []
        
        return {
            'league': league.upper(),
            'match_count': len(matches),
            'matches': matches,
            'odds': odds
        }


# Singleton instance
sports_feeder = SportsFeeder()
```

### Usage in `api/main.py`
```python
from api.services.sports_feed_service import sports_feeder

@router.get("/api/sports/feed")
async def get_unified_feed():
    """Get unified sports feed"""
    feed = sports_feeder.get_combined_feed()
    return feed

@router.get("/api/sports/feed/mlb")
async def get_mlb_feed(date: str = None):
    """Get MLB feed"""
    return sports_feeder.get_mlb_feed(date)

@router.get("/api/sports/feed/tennis/{league}")
async def get_tennis_feed(league: str = 'atp'):
    """Get tennis feed"""
    return sports_feeder.get_tennis_feed(league)
```

---

## 5. Environment Configuration

### File: `.env`
```
# The Odds API
ODDS_API_KEY=your_free_api_key_here

# Optional: Service configuration
MLB_STATS_ENABLED=true
TENNIS_ENABLED=true
ODDS_ENABLED=true

# Caching (seconds)
CACHE_TTL=300

# Rate limiting
REQUESTS_PER_MINUTE=60
```

### File: `api/services/env.py` (Update)
```python
import os

# Add to your env.py file
ODDS_API_KEY = os.getenv('ODDS_API_KEY')
MLB_STATS_ENABLED = os.getenv('MLB_STATS_ENABLED', 'true').lower() == 'true'
TENNIS_ENABLED = os.getenv('TENNIS_ENABLED', 'true').lower() == 'true'
ODDS_ENABLED = os.getenv('ODDS_ENABLED', 'true').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', 300))
```

---

## 6. Integration Tests

### File: `api/tests/test_sports_apis.py`

```python
"""
Tests for sports API integrations
"""

import unittest
from api.services.mlb_stats_service import mlb_service
from api.services.tennis_service import tennis_service
from api.services.odds_service import odds_service
from datetime import datetime


class TestMLBStatsService(unittest.TestCase):
    
    def test_get_schedule(self):
        """Test getting MLB schedule"""
        today = datetime.now().strftime('%Y-%m-%d')
        schedule = mlb_service.get_schedule(today)
        
        self.assertIsNotNone(schedule)
        self.assertIsInstance(schedule, list)
    
    def test_get_standings(self):
        """Test getting standings"""
        standings = mlb_service.get_standings()
        
        self.assertIsNotNone(standings)
        self.assertIsInstance(standings, list)


class TestTennisService(unittest.TestCase):
    
    def test_get_atp_matches(self):
        """Test getting ATP matches"""
        matches_data = tennis_service.get_atp_matches()
        
        self.assertIsNotNone(matches_data)
        self.assertIn('events', matches_data)
    
    def test_get_active_matches(self):
        """Test getting active matches"""
        active = tennis_service.get_active_matches('atp')
        
        self.assertIsNotNone(active)
        self.assertIsInstance(active, list)


class TestOddsService(unittest.TestCase):
    
    def test_get_sports(self):
        """Test getting available sports"""
        sports = odds_service.get_sports()
        
        self.assertIsNotNone(sports)
        self.assertIsInstance(sports, list)


if __name__ == '__main__':
    unittest.main()
```

---

## Quick Integration Steps

1. **Copy the services** to your `api/services/` directory
2. **Update** `.env` with your Odds API key
3. **Import** in `api/main.py`
4. **Test** the endpoints:
   ```bash
   curl http://localhost:8000/api/mlb/schedule/2025-06-15
   curl http://localhost:8000/api/tennis/atp/live
   curl http://localhost:8000/api/odds/mlb
   ```
5. **Deploy** to production

---

## Next Steps

- Implement caching using Redis for better performance
- Add error handling and fallback strategies
- Monitor API response times and quotas
- Plan upgrade path for Odds API if needed (from free to paid)

