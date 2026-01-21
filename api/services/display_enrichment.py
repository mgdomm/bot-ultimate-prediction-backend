from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import json

import hashlib
import urllib.request
from functools import lru_cache

# API-SPORTS a veces devuelve una imagen 'image not available' con HTTP 200.
# La detectamos por hash y devolvemos None para que el frontend haga fallback.
PLACEHOLDER_LOGO_SHA256 = "7670cc2d08b0b4a846ac6ec076c99d3767c4d2b9322e2d31cd05871422ddbbda"
API_SPORTS_MEDIA_HOST = "media.api-sports.io"

@lru_cache(maxsize=2048)
def _is_api_sports_placeholder_image(url: str) -> bool:
    if not url or API_SPORTS_MEDIA_HOST not in url:
        return False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = r.read()
        h = hashlib.sha256(data).hexdigest()
        return h == PLACEHOLDER_LOGO_SHA256
    except Exception:
        return False

def sanitize_logo_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    u = str(url)
    # Solo sanitizamos logos de API-SPORTS.
    if API_SPORTS_MEDIA_HOST in u and _is_api_sports_placeholder_image(u):
        return None
    return u



@dataclass(frozen=True)
class DisplayTeam:
    name: str
    logo: Optional[str] = None


def _repo_root() -> Path:
    # api/services/display_enrichment.py -> repo root es parents[2]
    return Path(__file__).resolve().parents[2]


def _events_dir(day: str) -> Path:
    return _repo_root() / "api" / "data" / "events" / day


def _safe_read_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _build_football_index(day: str) -> Dict[str, Dict[str, Any]]:
    """
    Indexa api/data/events/<day>/football.json (raw API-SPORTS) por eventId(str).
    Devuelve: eventId -> {home:{name,logo}, away:{name,logo}, league, startTime}
    """
    raw_path = _events_dir(day) / "football.json"
    data = _safe_read_json(raw_path)
    if not data:
        return {}

    response = data.get("response") if isinstance(data, dict) else None
    if not isinstance(response, list):
        return {}

    idx: Dict[str, Dict[str, Any]] = {}
    for item in response:
        if not isinstance(item, dict):
            continue
        fixture = item.get("fixture") if isinstance(item.get("fixture"), dict) else {}
        event_id = fixture.get("id")
        if event_id is None:
            continue

        teams = item.get("teams") if isinstance(item.get("teams"), dict) else {}
        home = teams.get("home") if isinstance(teams.get("home"), dict) else {}
        away = teams.get("away") if isinstance(teams.get("away"), dict) else {}

        league = item.get("league") if isinstance(item.get("league"), dict) else {}

        idx[str(event_id)] = {
            "sport": "football",
            "eventId": str(event_id),
            "league": league.get("name"),
            "leagueLogo": league.get("logo"),
            "startTime": fixture.get("date"),
            "home": {"name": home.get("name"), "logo": home.get("logo")},
            "away": {"name": away.get("name"), "logo": away.get("logo")},
        }

    return idx


def _build_generic_games_index(day: str, sport: str) -> Dict[str, Dict[str, Any]]:
    """
    Builder genérico para deportes donde response[] tiene:
      { id, date, league:{name,logo}, teams:{home:{name,logo}, away:{...}} }
    (handball/hockey/basketball/rugby/volleyball/baseball/afl suelen venir así)
    """
    raw_path = _events_dir(day) / f"{sport}.json"
    data = _safe_read_json(raw_path)
    if not data:
        return {}

    response = data.get("response") if isinstance(data, dict) else None
    if not isinstance(response, list):
        return {}

    idx: Dict[str, Dict[str, Any]] = {}
    for item in response:
        if not isinstance(item, dict):
            continue

        event_id = item.get("id")
        if event_id is None:
            continue

        league = item.get("league") if isinstance(item.get("league"), dict) else {}
        teams = item.get("teams") if isinstance(item.get("teams"), dict) else {}
        home = teams.get("home") if isinstance(teams.get("home"), dict) else {}
        away = teams.get("away") if isinstance(teams.get("away"), dict) else {}

        start_time = item.get("date")
        if isinstance(start_time, dict):
            d = start_time.get("date")
            t = start_time.get("time")
            start_time = f"{d}T{t}:00+00:00" if d and t else None

        idx[str(event_id)] = {
            "sport": sport,
            "eventId": str(event_id),
            "league": league.get("name"),
            "leagueLogo": league.get("logo"),
            "startTime": start_time,
            "home": {"name": home.get("name"), "logo": home.get("logo")},
            "away": {"name": away.get("name"), "logo": away.get("logo")},
        }

    return idx


def _build_nfl_index(day: str) -> Dict[str, Dict[str, Any]]:
    """
    NFL (american-football) viene como:
      { game:{id, date:{timestamp|date|time}}, league:{name,logo}, teams:{home,away} }
    """
    raw_path = _events_dir(day) / "nfl.json"
    data = _safe_read_json(raw_path)
    if not data:
        return {}

    response = data.get("response") if isinstance(data, dict) else None
    if not isinstance(response, list):
        return {}

    idx: Dict[str, Dict[str, Any]] = {}
    for item in response:
        if not isinstance(item, dict):
            continue

        game = item.get("game") if isinstance(item.get("game"), dict) else {}
        event_id = game.get("id")
        if event_id is None:
            continue

        league = item.get("league") if isinstance(item.get("league"), dict) else {}
        teams = item.get("teams") if isinstance(item.get("teams"), dict) else {}
        home = teams.get("home") if isinstance(teams.get("home"), dict) else {}
        away = teams.get("away") if isinstance(teams.get("away"), dict) else {}

        start_time = None
        date_info = game.get("date") if isinstance(game.get("date"), dict) else {}
        ts = date_info.get("timestamp")
        if ts is not None:
            try:
                start_time = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
            except Exception:
                start_time = None
        if not start_time:
            d = date_info.get("date")
            t = date_info.get("time")
            if d and t:
                start_time = f"{d}T{t}:00+00:00"

        idx[str(event_id)] = {
            "sport": "nfl",
            "eventId": str(event_id),
            "league": league.get("name"),
            "leagueLogo": league.get("logo"),
            "startTime": start_time,
            "home": {"name": home.get("name"), "logo": home.get("logo")},
            "away": {"name": away.get("name"), "logo": away.get("logo")},
        }

    return idx


def build_display_index(day: str) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Índice genérico multi-deporte:
      (sport, eventId) -> display_payload
    """
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}

    football = _build_football_index(day)
    for event_id, disp in football.items():
        out[("football", event_id)] = disp

    nfl = _build_nfl_index(day)
    for event_id, disp in nfl.items():
        out[("nfl", event_id)] = disp

    for sport in ["handball", "hockey", "basketball", "rugby", "volleyball", "baseball", "afl"]:
        idx = _build_generic_games_index(day, sport)
        for event_id, disp in idx.items():
            out[(sport, event_id)] = disp

    return out


def enrich_pick_inplace(pick: Dict[str, Any], display_index: Dict[Tuple[str, str], Dict[str, Any]]) -> None:
    """
    Inyecta pick["display"] si se puede resolver por (sport,eventId).
    NO borra nada.
    """
    sport = pick.get("sport")
    event_id = pick.get("eventId") or pick.get("event_id") or pick.get("fixtureId") or pick.get("fixture_id")
    if not sport or not event_id:
        return

    key = (str(sport), str(event_id))
    disp = display_index.get(key)
    if not disp:
        return

    home = disp.get("home") if isinstance(disp.get("home"), dict) else {}
    away = disp.get("away") if isinstance(disp.get("away"), dict) else {}
    pick["display"] = {
        "sport": disp.get("sport"),
        "eventId": disp.get("eventId"),
        "league": disp.get("league"),
        "leagueLogo": sanitize_logo_url(disp.get("leagueLogo")),
        "startTime": disp.get("startTime"),
        "home": {"name": home.get("name"), "logo": sanitize_logo_url(home.get("logo"))},
        "away": {"name": away.get("name"), "logo": sanitize_logo_url(away.get("logo"))},
    }


def _enrich_parlay_container_inplace(container: Dict[str, Any], display_index: Dict[Tuple[str, str], Dict[str, Any]]) -> None:
    """
    Enriquecer un objeto parlay tipo:
      { legs: [pick, pick, ...] }
    (también soporta la clave 'picks' por compatibilidad).
    """
    if not isinstance(container, dict):
        return

    legs = container.get("legs")
    if not isinstance(legs, list):
        legs = container.get("picks")
    if not isinstance(legs, list):
        return

    for leg in legs:
        if isinstance(leg, dict):
            enrich_pick_inplace(leg, display_index)


def enrich_contract_inplace(contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enriquecimiento determinista del contrato usando snapshots locales.
    """
    day = contract.get("contract_date")
    if not day:
        return contract

    display_index = build_display_index(day)

    # picks_classic: lista de contenedores; cada contenedor puede ser lista de picks
    picks_classic = contract.get("picks_classic") or []
    for container in picks_classic:
        if isinstance(container, list):
            for pick in container:
                if isinstance(pick, dict):
                    enrich_pick_inplace(pick, display_index)
        elif isinstance(container, dict):
            enrich_pick_inplace(container, display_index)

    # picks_parlay_premium: lista de parleys; cada uno tiene legs/picks
    picks_parlay = contract.get("picks_parlay_premium") or []
    if isinstance(picks_parlay, list):
        for parlay in picks_parlay:
            if isinstance(parlay, dict):
                _enrich_parlay_container_inplace(parlay, display_index)

    # daily_featured_parlay: dict con legs/picks
    featured = contract.get("daily_featured_parlay")
    if isinstance(featured, dict):
        _enrich_parlay_container_inplace(featured, display_index)

    return contract
