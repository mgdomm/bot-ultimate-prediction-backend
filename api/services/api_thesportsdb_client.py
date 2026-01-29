"""
DF_THESPORTSDB_CLIENT: Cliente para TheSportsDB (gratis)

Cobertura: múltiples deportes (logos y eventos del día)
- Live: livescore.php?s={sport}
- Day events: eventsday.php?d=YYYY-MM-DD&s={sport}
- Team logos: lookupteam.php?t={team}
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


class TheSportsDBClient:
    BASE_URL = "https://www.thesportsdb.com/api/v1/json"
    FREE_KEY = os.environ.get("THESPORTSDB_KEY", "3")  # clave gratuita pública
    TIMEOUT = 15

    # Map our sports to TheSportsDB sport names
    SPORT_NAME_MAP = {
        "soccer": "Soccer",
        "football": "Soccer",
        "rugby": "Rugby",
        "rugby-league": "Rugby League",
        "american-football": "American Football",
        "nfl": "American Football",
        "basketball": "Basketball",
        "hockey": "Ice Hockey",
        "handball": "Handball",
        "volleyball": "Volleyball",
        "afl": "Australian Football",
        "tennis": "Tennis",
        "baseball": "Baseball",
        "mma": "MMA",
        "f1": "Motorsport",
    }

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            repo_root = Path(__file__).resolve().parents[2]
            cache_dir = repo_root / "api" / "data" / ".thesportsdb_cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.teams_cache_path = self.cache_dir / "teams.json"
        self._teams_cache = self._load_team_cache()

    def _load_team_cache(self) -> Dict[str, Dict[str, Any]]:
        if not self.teams_cache_path.exists():
            return {}
        try:
            return json.loads(self.teams_cache_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_team_cache(self) -> None:
        try:
            self.teams_cache_path.write_text(json.dumps(self._teams_cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _sport_name(self, sport: str) -> Optional[str]:
        return self.SPORT_NAME_MAP.get(sport.lower())

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{self.FREE_KEY}/{path.lstrip('/')}"
        r = requests.get(url, params=params or {}, timeout=self.TIMEOUT)
        r.raise_for_status()
        return r.json() if r.content else {}

    def get_team_logo(self, team_name: str) -> Optional[str]:
        if not team_name:
            return None
        key = team_name.strip().lower()
        cached = self._teams_cache.get(key)
        if isinstance(cached, dict):
            return cached.get("logo")

        try:
            # lookupteam.php?t={team}
            payload = self._get("lookupteam.php", {"t": team_name})
            teams = payload.get("teams") if isinstance(payload, dict) else None
            if isinstance(teams, list) and teams:
                team = teams[0]
                logo = team.get("strTeamBadge") or team.get("strBadge") or team.get("strLogo")
                self._teams_cache[key] = {"logo": logo}
                self._save_team_cache()
                return logo
        except Exception as e:
            logger.debug(f"[thesportsdb] logo lookup failed for {team_name}: {e}")

        self._teams_cache[key] = {"logo": None}
        self._save_team_cache()
        return None

    def get_live_events(self, sport: str, date: str) -> List[Dict[str, Any]]:
        sport_name = self._sport_name(sport)
        if not sport_name:
            return []

        events: List[Dict[str, Any]] = []

        # Try livescore first
        try:
            payload = self._get("livescore.php", {"s": sport_name})
            events = self._normalize_events(payload.get("events"), sport, date)
            if events:
                return events
        except Exception as e:
            logger.debug(f"[thesportsdb] livescore failed {sport}: {e}")

        # Fallback to eventsday
        try:
            payload = self._get("eventsday.php", {"d": date, "s": sport_name})
            events = self._normalize_events(payload.get("events"), sport, date)
        except Exception as e:
            logger.debug(f"[thesportsdb] eventsday failed {sport}: {e}")

        return events

    def _normalize_events(self, raw_events: Any, sport: str, date: str) -> List[Dict[str, Any]]:
        if not isinstance(raw_events, list):
            return []
        out: List[Dict[str, Any]] = []
        for ev in raw_events:
            if not isinstance(ev, dict):
                continue
            event_id = ev.get("idEvent") or ev.get("id")
            home = ev.get("strHomeTeam") or ev.get("homeTeam")
            away = ev.get("strAwayTeam") or ev.get("awayTeam")
            if not event_id or not home or not away:
                continue
            date_event = ev.get("dateEvent") or date
            time_event = ev.get("strTime") or "00:00:00"
            start_time = f"{date_event}T{time_event}+00:00"

            home_logo = self.get_team_logo(home)
            away_logo = self.get_team_logo(away)

            status = ev.get("strStatus") or ev.get("strStatusShort") or ev.get("strStatus")
            live = {
                "homeScore": ev.get("intHomeScore"),
                "awayScore": ev.get("intAwayScore"),
                "status": status,
                "statusShort": status,
                "timer": ev.get("strProgress"),
            }

            out.append(
                {
                    "sport": sport,
                    "eventId": str(event_id),
                    "home": {"name": home, "logo": home_logo},
                    "away": {"name": away, "logo": away_logo},
                    "startTime": start_time,
                    "league": ev.get("strLeague"),
                    "live": live,
                }
            )
        return out
