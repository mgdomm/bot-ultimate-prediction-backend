from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from services.api_sports_client import ApiSportsClient  # type: ignore
    from services.api_theodds_cached import TheOddsAPICached  # type: ignore
except ModuleNotFoundError:
    from api.services.api_sports_client import ApiSportsClient  # type: ignore
    from api.services.api_theodds_cached import TheOddsAPICached  # type: ignore

logger = logging.getLogger(__name__)

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"

# FREE: mantener bajo para evitar rateLimit/min (se puede override con ODDS_MAX_EVENTS_PER_SPORT)
MAX_EVENTS_PER_SPORT_DEFAULT = 8

# Estrategia odds por deporte - SOLO The Odds API (9 deportes verificables)
# NO incluimos Handball, Volleyball, MMA, F1 (cálculos internos sin confianza)
ODDS_MODE_BY_SPORT: Dict[str, Dict[str, str]] = {
    # The Odds API FREE tier - SOLO ESTOS 9 deportes
    "football": {"mode": "theodds_api", "odds_sport": "soccer"},
    "soccer": {"mode": "theodds_api", "odds_sport": "soccer"},
    "rugby": {"mode": "theodds_api", "odds_sport": "rugby"},
    "rugby-league": {"mode": "theodds_api", "odds_sport": "rugby"},
    "american-football": {"mode": "theodds_api", "odds_sport": "nfl"},
    "nfl": {"mode": "theodds_api", "odds_sport": "nfl"},
    "basketball": {"mode": "theodds_api", "odds_sport": "basketball"},
    "hockey": {"mode": "theodds_api", "odds_sport": "hockey"},
    "tennis": {"mode": "theodds_api", "odds_sport": "tennis"},
    "baseball": {"mode": "theodds_api", "odds_sport": "baseball"},
    "afl": {"mode": "theodds_api", "odds_sport": "afl"},
    # REMOVIDOS (sin confianza):
    # "handball": {...},
    # "volleyball": {...},
    # "mma": {...},
    # "f1": {...},
}


@dataclass(frozen=True)
class OddsIngestSummary:
    sport: str
    status: str  # created | skipped | rate_limited
    file: str
    requested: int
    nonzero_results: int


def _first_list(payload: dict) -> List[dict]:
    resp = payload.get("response")
    return resp if isinstance(resp, list) else []


def _extract_event_id(sport: str, item: dict) -> Optional[int]:
    if sport == "football":
        x = (item.get("fixture") or {}).get("id")
        return int(x) if x is not None else None
    if sport == "nfl":
        g = item.get("game")
        if isinstance(g, dict) and g.get("id") is not None:
            return int(g["id"])
    x = item.get("id")
    return int(x) if x is not None else None


def _event_status_short(sport: str, item: dict) -> Optional[str]:
    # Intento “best-effort” sin asumir estructura fija
    if sport == "football":
        st = (item.get("fixture") or {}).get("status") or {}
        if isinstance(st, dict):
            v = st.get("short")
            return str(v) if v is not None else None
        return None
    # otros deportes (algunos usan game.status o status)
    st = item.get("status")
    if st is not None:
        return str(st)
    g = item.get("game")
    if isinstance(g, dict) and g.get("status") is not None:
        return str(g.get("status"))
    return None


def _is_candidate_event(sport: str, item: dict) -> bool:
    # Filtra eventos claramente no jugables (cancelados/postpuestos/finalizados)
    bad = {"FT", "AET", "PEN", "CANC", "PST", "ABD", "CANCELLED", "POSTPONED", "ABANDONED", "FINISHED"}
    st = _event_status_short(sport, item)
    if st is not None and st.upper() in bad:
        return False

    # Preferimos eventos con liga/competición (suele correlacionar con odds disponibles)
    league = item.get("league")
    if isinstance(league, dict):
        if league.get("id") is not None or league.get("name"):
            return True

    # Si no hay league, no descartamos: dejamos pasar igual
    return True


def _load_event_ids(day: str, sport: str) -> List[int]:
    """
    Devuelve IDs en un orden "mejor" que sorted():
    - preserva el orden de los eventos en el archivo (la API suele traer por schedule/importancia)
    - filtra eventos claramente no jugables (canceled/postponed/finished)
    - unique estable
    """
    p = API_DATA_DIR / "events" / day / f"{sport}.json"
    if not p.exists():
        return []

    payload = json.loads(p.read_text(encoding="utf-8"))
    seen: set[int] = set()
    out: List[int] = []

    for item in _first_list(payload):
        if not isinstance(item, dict):
            continue
        if not _is_candidate_event(sport, item):
            continue
        eid = _extract_event_id(sport, item)
        if eid is None:
            continue
        if eid in seen:
            continue
        seen.add(eid)
        out.append(eid)

    return out


def _is_rate_limit_exc(exc: BaseException) -> bool:
    s = str(exc)
    if "rateLimit" in s or "Too many requests" in s:
        return True
    # requests.HTTPError (si viene por status_code)
    resp = getattr(exc, "response", None)
    code = getattr(resp, "status_code", None)
    return code == 429


def ingest_odds_for_day(
    day: Optional[str] = None,
    force: bool = False,
    sports: Optional[List[str]] = None,
    max_events_per_sport: int = MAX_EVENTS_PER_SPORT_DEFAULT,
) -> Dict[str, Any]:
    """
    Ingest odds for a day - HYBRID approach
    
    Strategy:
    1. The Odds API FREE (500 req/month) for 9 sports with real market odds
    2. Internal estimation for 3 sports not supported by The Odds API
    
    Result: 12 sports covered, realistic odds, cost = $0
    """
    if day is None:
        day = date.today().isoformat()

    out_dir = API_DATA_DIR / "odds" / day
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = sorted(ODDS_MODE_BY_SPORT.keys()) if not sports else sports
    unknown = [s for s in selected if s not in ODDS_MODE_BY_SPORT]
    if unknown:
        raise SystemExit(f"Unknown sports: {unknown}. Allowed: {sorted(ODDS_MODE_BY_SPORT.keys())}")

    summary: Dict[str, Any] = {
        "day": day,
        "force": force,
        "strategy": "THEODDS_API_ONLY_9_SPORTS",
        "sports_selected": selected,
        "max_events_per_sport": max_events_per_sport,
        "sports": [],
    }

    # Initialize The Odds API client with caching (FREE tier, 500 req/month)
    # Caching ensures we fetch all odds ONCE per day, not multiple times per hour
    theodds_client = TheOddsAPICached()
    
    # Fetch all odds for the day (uses cache if fresh)
    logger.info(f"Fetching odds for {day} (uses caching to reduce API quota)")
    all_odds = theodds_client.fetch_all_odds(day, force_refresh=force)
    
    theodds_sports_used = []

    for sport in selected:
        conf = ODDS_MODE_BY_SPORT[sport]
        out_file = out_dir / f"{sport}.json"
        
        if out_file.exists() and not force:
            summary["sports"].append(OddsIngestSummary(sport, "skipped", str(out_file), 0, 0).__dict__)
            continue

        try:
            mode = conf.get("mode", "theodds_api")
            
            # Use The Odds API for real betting odds (9 verified sports ONLY)
            if mode == "theodds_api":
                odds_sport = conf.get("odds_sport", sport)
                
                # Get from cached result
                events = all_odds.get(odds_sport, [])
                
                payload = {
                    "sport": sport,
                    "day": day,
                    "source": "theodds_api_cached",
                    "strategy": "real_market_odds_cached",
                    "results": len(events),
                    "response": events,
                    "bookmakers": ["draftkings", "fanduel", "betmgm", "betrivers"],
                }
                
                out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                summary["sports"].append(OddsIngestSummary(sport, "created", str(out_file), 1, len(events)).__dict__)
                theodds_sports_used.append(sport)
                continue

        except Exception as e:
            logger.error(f"Error processing {sport}: {e}")
            summary["sports"].append(OddsIngestSummary(sport, "error", str(out_file), 0, 0).__dict__)

    # Log summary
    summary["theodds_api_sports_used"] = theodds_sports_used
    summary["sports_count"] = len(theodds_sports_used)
    summary["note"] = "Odds fetched once per day and cached to conserve The Odds API quota"

    return summary


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest odds multisport into api/data/odds/<day>/<sport>.json")
    p.add_argument("day", nargs="?", default=None, help="YYYY-MM-DD (default: today)")
    p.add_argument("--force", action="store_true", help="Regenerate even if output files already exist")
    p.add_argument(
        "--sports",
        default=None,
        help=f"Comma-separated subset (default: all) Allowed: {','.join(sorted(ODDS_MODE_BY_SPORT.keys()))}",
    )
    p.add_argument(
        "--max-events",
        type=int,
        default=MAX_EVENTS_PER_SPORT_DEFAULT,
        help=f"Max event-requests per sport in per_event mode (default: {MAX_EVENTS_PER_SPORT_DEFAULT})",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    sports = [s.strip() for s in args.sports.split(',') if s.strip()] if args.sports else None
    summary = ingest_odds_for_day(
        day=args.day,
        force=bool(args.force),
        sports=sports,
        max_events_per_sport=int(args.max_events),
    )
    # Log compacto (Render trunca; queremos ver downstream: classic + FREEZE)
    compact = {
        'day': summary.get('day'),
        'force': summary.get('force'),
        'max_events_per_sport': summary.get('max_events_per_sport'),
        'sports_selected': summary.get('sports_selected'),
        'sports': [
            {
                'sport': s.get('sport'),
                'status': s.get('status'),
                'requested': s.get('requested'),
                'nonzero_results': s.get('nonzero_results'),
            }
            for s in (summary.get('sports') or [])
        ],
    }
    print(json.dumps(compact, ensure_ascii=False))
