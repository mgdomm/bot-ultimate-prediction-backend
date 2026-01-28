"""
DF_APIS_ALTERNATIVES: Clientes para APIs públicas gratuitas (sin autenticación)

Cobertura:
- NBA: balldontlie
- NHL: NHL Stats API (unofficial)
- Handball: OpenLigaDB
- Volleyball: OpenLigaDB
- AFL: Squiggle
"""

import requests
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


class BalldontlieClient:
    """NBA live events via balldontlie API (no auth required)"""
    
    BASE_URL = "https://api.balldontlie.io/v1"
    TIMEOUT = 15
    
    @staticmethod
    def get_games(date: str) -> List[Dict[str, Any]]:
        """
        Fetch NBA games for a specific date (YYYY-MM-DD)
        Returns list of game objects with live data
        """
        try:
            url = f"{BalldontlieClient.BASE_URL}/games"
            params = {"date": date}
            response = requests.get(url, params=params, timeout=BalldontlieClient.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            games = data.get("data", [])
            return [BalldontlieClient._normalize_game(g) for g in games]
        except Exception as e:
            print(f"[balldontlie] Error fetching games: {e}")
            return []
    
    @staticmethod
    def _normalize_game(game: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize balldontlie game to standard format"""
        return {
            "sport": "basketball",
            "eventId": str(game.get("id", "")),
            "home": {
                "name": game.get("home_team", {}).get("name", ""),
                "id": game.get("home_team", {}).get("id"),
            },
            "away": {
                "name": game.get("visitor_team", {}).get("name", ""),
                "id": game.get("visitor_team", {}).get("id"),
            },
            "startTime": game.get("date"),
            "live": {
                "homeScore": game.get("home_team_score"),
                "awayScore": game.get("visitor_team_score"),
                "status": game.get("status"),
                "statusShort": "FT" if game.get("status") == "Final" else (
                    "LIVE" if game.get("status") == "In Progress" else "SCHEDULED"
                ),
            }
        }


class NHLStatsClient:
    """NHL live events via StatsAPI (no auth required)"""
    
    BASE_URL = "https://statsapi.web.nhl.com/api/v1"
    TIMEOUT = 15
    
    @staticmethod
    def get_games(date: str) -> List[Dict[str, Any]]:
        """
        Fetch NHL games for a specific date (YYYY-MM-DD)
        """
        try:
            url = f"{NHLStatsClient.BASE_URL}/schedule"
            params = {"startDate": date, "endDate": date}
            response = requests.get(url, params=params, timeout=NHLStatsClient.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            games = data.get("games", [])
            return [NHLStatsClient._normalize_game(g) for g in games]
        except Exception as e:
            print(f"[nhl-stats] Error fetching games: {e}")
            return []
    
    @staticmethod
    def _normalize_game(game: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize NHL game to standard format"""
        teams = game.get("teams", {})
        away = teams.get("away", {})
        home = teams.get("home", {})
        
        status_map = {
            "Scheduled": "SCHEDULED",
            "In Progress": "LIVE",
            "Live": "LIVE",
            "Final": "FT",
            "In Progress - Critical": "LIVE",
        }
        
        return {
            "sport": "hockey",
            "eventId": str(game.get("gamePk", "")),
            "home": {
                "name": home.get("team", {}).get("name", ""),
                "id": home.get("team", {}).get("id"),
            },
            "away": {
                "name": away.get("team", {}).get("name", ""),
                "id": away.get("team", {}).get("id"),
            },
            "startTime": game.get("gameDateTime"),
            "live": {
                "homeScore": home.get("score"),
                "awayScore": away.get("score"),
                "status": game.get("status", {}).get("detailedState"),
                "statusShort": status_map.get(
                    game.get("status", {}).get("abstractGameState", "Scheduled"),
                    "SCHEDULED"
                ),
                "timer": game.get("status", {}).get("abstractGameState"),
            }
        }


class OpenLigaDBClient:
    """OpenLigaDB for Handball and Volleyball (no auth required)"""
    
    BASE_URL = "https://www.openligadb.de/api"
    TIMEOUT = 15
    
    LEAGUE_MAP = {
        "handball": "HBL",  # German Handball League
        "volleyball": "VBL",  # German Volleyball League
    }
    
    @staticmethod
    def get_games(sport: str, date: str) -> List[Dict[str, Any]]:
        """
        Fetch games for handball or volleyball on a specific date (YYYY-MM-DD)
        """
        league_code = OpenLigaDBClient.LEAGUE_MAP.get(sport.lower())
        if not league_code:
            return []
        
        try:
            url = f"{OpenLigaDBClient.BASE_URL}/getmatchinformation"
            params = {"leagueShortcut": league_code}
            response = requests.get(url, params=params, timeout=OpenLigaDBClient.TIMEOUT)
            response.raise_for_status()
            matches = response.json()
            
            if not isinstance(matches, list):
                return []
            
            # Filter by date
            target_date = datetime.fromisoformat(date).date()
            filtered = [
                m for m in matches
                if m.get("MatchDateTime") and datetime.fromisoformat(m["MatchDateTime"]).date() == target_date
            ]
            
            return [OpenLigaDBClient._normalize_match(m, sport) for m in filtered]
        except Exception as e:
            print(f"[openligadb] Error fetching {sport} games: {e}")
            return []
    
    @staticmethod
    def _normalize_match(match: Dict[str, Any], sport: str) -> Dict[str, Any]:
        """Normalize OpenLigaDB match to standard format"""
        status_map = {
            "Scheduled": "SCHEDULED",
            "InProgress": "LIVE",
            "Finished": "FT",
        }
        
        return {
            "sport": sport,
            "eventId": str(match.get("MatchID", "")),
            "home": {
                "name": match.get("Team1", {}).get("TeamName", ""),
                "id": match.get("Team1", {}).get("TeamId"),
            },
            "away": {
                "name": match.get("Team2", {}).get("TeamName", ""),
                "id": match.get("Team2", {}).get("TeamId"),
            },
            "startTime": match.get("MatchDateTime"),
            "live": {
                "homeScore": match.get("MatchResults", [{}])[0].get("PointsTeam1") if match.get("MatchResults") else None,
                "awayScore": match.get("MatchResults", [{}])[0].get("PointsTeam2") if match.get("MatchResults") else None,
                "status": match.get("MatchIsFinished"),
                "statusShort": status_map.get(match.get("MatchStateID", ""), "SCHEDULED"),
            }
        }


class SquiggleClient:
    """AFL (Australian Football League) via Squiggle API (no auth required)"""
    
    BASE_URL = "https://api.squiggle.com.au"
    TIMEOUT = 15
    
    @staticmethod
    def get_games(date: str) -> List[Dict[str, Any]]:
        """
        Fetch AFL games for a specific date (YYYY-MM-DD)
        """
        try:
            # Squiggle uses year and round, need to calculate from date
            url = f"{SquiggleClient.BASE_URL}/games"
            response = requests.get(url, timeout=SquiggleClient.TIMEOUT)
            response.raise_for_status()
            games = response.json()
            
            if not isinstance(games, list):
                return []
            
            # Filter by date
            target_date = datetime.fromisoformat(date).date()
            filtered = [
                g for g in games
                if g.get("date") and datetime.fromisoformat(g["date"]).date() == target_date
            ]
            
            return [SquiggleClient._normalize_game(g) for g in filtered]
        except Exception as e:
            print(f"[squiggle] Error fetching games: {e}")
            return []
    
    @staticmethod
    def _normalize_game(game: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Squiggle game to standard format"""
        complete = game.get("complete", False)
        
        return {
            "sport": "afl",
            "eventId": str(game.get("id", "")),
            "home": {
                "name": game.get("hteam", ""),
                "id": game.get("hteamid"),
            },
            "away": {
                "name": game.get("ateam", ""),
                "id": game.get("ateamid"),
            },
            "startTime": game.get("date"),
            "live": {
                "homeScore": game.get("hgoals") if complete else None,
                "awayScore": game.get("agoals") if complete else None,
                "status": "Finished" if complete else "Scheduled",
                "statusShort": "FT" if complete else "SCHEDULED",
            }
        }


class AlternativeApisClient:
    """Unified client for all alternative sports APIs"""
    
    SPORT_CLIENT_MAP = {
        "basketball": BalldontlieClient,
        "hockey": NHLStatsClient,
        "handball": OpenLigaDBClient,
        "volleyball": OpenLigaDBClient,
        "afl": SquiggleClient,
    }
    
    @staticmethod
    def get_live_events(sport: str, date: str) -> List[Dict[str, Any]]:
        """Get live events for a sport on a specific date"""
        client_class = AlternativeApisClient.SPORT_CLIENT_MAP.get(sport.lower())
        
        if not client_class:
            print(f"[alternatives] Sport {sport} not supported")
            return []
        
        if sport.lower() in ("handball", "volleyball"):
            return client_class.get_games(sport, date)
        else:
            return client_class.get_games(date)
    
    @staticmethod
    def get_all_sports_events(date: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get live events for all supported alternative sports"""
        result = {}
        
        for sport in ["basketball", "hockey", "handball", "volleyball", "afl"]:
            events = AlternativeApisClient.get_live_events(sport, date)
            if events:
                result[sport] = events
                print(f"[alternatives] {sport}: {len(events)} events")
        
        return result


if __name__ == "__main__":
    # Test
    today = datetime.now().isoformat()[:10]
    
    print(f"Fetching events for {today}...")
    
    # NBA
    nba_games = BalldontlieClient.get_games(today)
    print(f"NBA: {len(nba_games)} games")
    
    # NHL
    nhl_games = NHLStatsClient.get_games(today)
    print(f"NHL: {len(nhl_games)} games")
    
    # Handball
    hb_games = OpenLigaDBClient.get_games("handball", today)
    print(f"Handball: {len(hb_games)} games")
    
    # Volleyball
    vb_games = OpenLigaDBClient.get_games("volleyball", today)
    print(f"Volleyball: {len(vb_games)} games")
    
    # AFL
    afl_games = SquiggleClient.get_games(today)
    print(f"AFL: {len(afl_games)} games")
