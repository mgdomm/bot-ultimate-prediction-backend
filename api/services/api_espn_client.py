"""
DF_ESPN_CLIENTS: Clientes para APIs públicas de ESPN (sin autenticación)

Cobertura:
- Soccer/Football: ESPN hidden API (winners-table method)
- Rugby: ESPN Rugby API
- NFL: ESPN Sports API documentada
"""

import requests
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


class ESPNSoccerClient:
    """Soccer/Football live events via ESPN hidden API (no auth required)
    
    Uses the public endpoint from winners-table project:
    https://github.com/joelljones/winners-table
    """
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard"
    TIMEOUT = 15
    
    @staticmethod
    def get_games(date: str) -> List[Dict[str, Any]]:
        """
        Fetch soccer/football games for a specific date (YYYY-MM-DD)
        
        Date format: dates=YYYYMMDD (ESPN format)
        """
        try:
            # Convert date to ESPN format (YYYYMMDD)
            date_obj = datetime.fromisoformat(date)
            espn_date = date_obj.strftime("%Y%m%d")
            
            url = f"{ESPNSoccerClient.BASE_URL}"
            params = {"dates": espn_date}
            
            response = requests.get(url, params=params, timeout=ESPNSoccerClient.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("events", [])
            return [ESPNSoccerClient._normalize_event(e) for e in events]
        except Exception as e:
            print(f"[espn-soccer] Error fetching games: {e}")
            return []
    
    @staticmethod
    def _normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize ESPN soccer event to standard format"""
        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        home = competitors[0] if len(competitors) > 0 else {}
        away = competitors[1] if len(competitors) > 1 else {}
        
        competition = event.get("competitions", [{}])[0]
        status = competition.get("status", {})
        
        return {
            "sport": "football",
            "eventId": event.get("id", ""),
            "home": {
                "name": home.get("team", {}).get("displayName", ""),
                "id": home.get("team", {}).get("id"),
            },
            "away": {
                "name": away.get("team", {}).get("displayName", ""),
                "id": away.get("team", {}).get("id"),
            },
            "startTime": event.get("date"),
            "league": competition.get("league", {}).get("displayName", ""),
            "live": {
                "homeScore": home.get("score"),
                "awayScore": away.get("score"),
                "status": status.get("type"),
                "statusShort": ESPNSoccerClient._map_status(status.get("type", "")),
                "timer": status.get("displayClock"),
            }
        }
    
    @staticmethod
    def _map_status(status_type: str) -> str:
        """Map ESPN status type to standard format"""
        status_map = {
            "pre": "SCHEDULED",
            "in": "LIVE",
            "post": "FT",
            "final": "FT",
            "halftime": "HT",
            "STATUS_SCHEDULED": "SCHEDULED",
            "STATUS_IN_PROGRESS": "LIVE",
            "STATUS_FINAL": "FT",
        }
        return status_map.get(status_type, "SCHEDULED")


class ESPNRugbyClient:
    """Rugby live events via ESPN API
    
    Note: Rugby coverage via ESPN is limited. This attempts to fetch from
    the general ESPN sports API endpoints where available.
    """
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
    TIMEOUT = 15
    
    # Rugby league mappings (if ESPN supports them)
    RUGBY_LEAGUES = [
        "rugby/union",  # International rugby
        "rugby/league",  # Rugby league
    ]
    
    @staticmethod
    def get_games(date: str) -> List[Dict[str, Any]]:
        """
        Fetch rugby games for a specific date (YYYY-MM-DD)
        
        Note: ESPN rugby coverage is limited compared to soccer/NFL.
        May return empty list if no data available.
        """
        try:
            date_obj = datetime.fromisoformat(date)
            espn_date = date_obj.strftime("%Y%m%d")
            
            all_games = []
            
            for league in ESPNRugbyClient.RUGBY_LEAGUES:
                try:
                    url = f"{ESPNRugbyClient.BASE_URL}/{league}/scoreboard"
                    params = {"dates": espn_date}
                    
                    response = requests.get(url, params=params, timeout=ESPNRugbyClient.TIMEOUT)
                    if response.status_code == 404:
                        # League not available
                        continue
                    response.raise_for_status()
                    
                    data = response.json()
                    events = data.get("events", [])
                    all_games.extend([ESPNRugbyClient._normalize_event(e, league) for e in events])
                except Exception as e:
                    print(f"[espn-rugby] Error fetching {league}: {e}")
                    continue
            
            return all_games
        except Exception as e:
            print(f"[espn-rugby] Error: {e}")
            return []
    
    @staticmethod
    def _normalize_event(event: Dict[str, Any], league: str) -> Dict[str, Any]:
        """Normalize ESPN rugby event to standard format"""
        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        home = competitors[0] if len(competitors) > 0 else {}
        away = competitors[1] if len(competitors) > 1 else {}
        
        competition = event.get("competitions", [{}])[0]
        status = competition.get("status", {})
        
        # Map league type
        sport = "rugby"
        if "league" in league.lower():
            sport = "rugby-league"
        
        return {
            "sport": sport,
            "eventId": event.get("id", ""),
            "home": {
                "name": home.get("team", {}).get("displayName", ""),
                "id": home.get("team", {}).get("id"),
            },
            "away": {
                "name": away.get("team", {}).get("displayName", ""),
                "id": away.get("team", {}).get("id"),
            },
            "startTime": event.get("date"),
            "league": competition.get("league", {}).get("displayName", ""),
            "live": {
                "homeScore": home.get("score"),
                "awayScore": away.get("score"),
                "status": status.get("type"),
                "statusShort": ESPNSoccerClient._map_status(status.get("type", "")),
                "timer": status.get("displayClock"),
            }
        }


class ESPNNFLClient:
    """NFL live events via ESPN Sports API"""
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
    TIMEOUT = 15
    
    @staticmethod
    def get_games(date: str) -> List[Dict[str, Any]]:
        """
        Fetch NFL games for a specific date (YYYY-MM-DD)
        """
        try:
            # Convert date to ESPN format (YYYYMMDD)
            date_obj = datetime.fromisoformat(date)
            espn_date = date_obj.strftime("%Y%m%d")
            
            url = ESPNNFLClient.BASE_URL
            params = {"dates": espn_date}
            
            response = requests.get(url, params=params, timeout=ESPNNFLClient.TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("events", [])
            return [ESPNNFLClient._normalize_event(e) for e in events]
        except Exception as e:
            print(f"[espn-nfl] Error fetching games: {e}")
            return []
    
    @staticmethod
    def _normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize ESPN NFL event to standard format"""
        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        home = competitors[0] if len(competitors) > 0 else {}
        away = competitors[1] if len(competitors) > 1 else {}
        
        competition = event.get("competitions", [{}])[0]
        status = competition.get("status", {})
        
        return {
            "sport": "american-football",
            "eventId": event.get("id", ""),
            "home": {
                "name": home.get("team", {}).get("displayName", ""),
                "id": home.get("team", {}).get("id"),
            },
            "away": {
                "name": away.get("team", {}).get("displayName", ""),
                "id": away.get("team", {}).get("id"),
            },
            "startTime": event.get("date"),
            "league": competition.get("league", {}).get("displayName", ""),
            "live": {
                "homeScore": home.get("score"),
                "awayScore": away.get("score"),
                "status": status.get("type"),
                "statusShort": ESPNSoccerClient._map_status(status.get("type", "")),
                "timer": status.get("displayClock"),
            }
        }


class ESPNClient:
    """Unified ESPN client for all sports"""
    
    SPORT_CLIENT_MAP = {
        "football": ESPNSoccerClient,
        "soccer": ESPNSoccerClient,
        "rugby": ESPNRugbyClient,
        "rugby-league": ESPNRugbyClient,
        "american-football": ESPNNFLClient,
        "nfl": ESPNNFLClient,
    }
    
    @staticmethod
    def get_live_events(sport: str, date: str) -> List[Dict[str, Any]]:
        """Get live events for a sport on a specific date"""
        client_class = ESPNClient.SPORT_CLIENT_MAP.get(sport.lower())
        
        if not client_class:
            print(f"[espn] Sport {sport} not supported")
            return []
        
        return client_class.get_games(date)


if __name__ == "__main__":
    # Test
    today = datetime.now().isoformat()[:10]
    
    print(f"Fetching events for {today}...")
    
    # Soccer
    soccer_games = ESPNSoccerClient.get_games(today)
    print(f"Soccer: {len(soccer_games)} games")
    
    # Rugby
    rugby_games = ESPNRugbyClient.get_games(today)
    print(f"Rugby: {len(rugby_games)} games")
    
    # NFL
    nfl_games = ESPNNFLClient.get_games(today)
    print(f"NFL: {len(nfl_games)} games")
