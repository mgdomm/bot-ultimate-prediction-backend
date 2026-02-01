from __future__ import annotations

# Load .env at the very beginning
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from services.api_sports_client import ApiSportsClient  # type: ignore
    from services.api_oddsapiio_client import OddsAPIIOClient  # type: ignore
    from services.api_sportsgameodds_client import SportsGameOddsClient  # type: ignore
except ModuleNotFoundError:
    from api.services.api_sports_client import ApiSportsClient  # type: ignore
    from api.services.api_oddsapiio_client import OddsAPIIOClient  # type: ignore
    from api.services.api_sportsgameodds_client import SportsGameOddsClient  # type: ignore

logger = logging.getLogger(__name__)

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def _parse_american_odds(odds_str: str) -> float:
    """Convert American odds string (+110, -110) to decimal odds"""
    try:
        if isinstance(odds_str, (int, float)):
            odds_num = float(odds_str)
            # If it looks like decimal already (< 10), return as-is
            if 0.5 < odds_num < 20:
                return odds_num
            # Otherwise treat as american odds
            if odds_num >= 100:  # Positive american odds
                return 1 + (odds_num / 100)
            else:  # Negative american odds
                return 1 + (100 / abs(odds_num))
        
        odds_str = str(odds_str).strip()
        odds_num = float(odds_str.replace("+", ""))
        
        if odds_num >= 100:  # Positive american odds
            return 1 + (odds_num / 100)
        else:  # Negative american odds
            return 1 + (100 / abs(odds_num))
    except:
        return 1.0  # Default fallback


# FREE: mantener bajo para evitar rateLimit/min (se puede override con ODDS_MAX_EVENTS_PER_SPORT)
MAX_EVENTS_PER_SPORT_DEFAULT = 8

# Estrategia odds por deporte - MIGRADO A SportsGameOdds.com (FREE tier: 8 deportes, 9 bookmakers)
# SportsGameOdds: 2,500 objetos/mes, 10 req/min, 10 min update frequency
# Strategy: 1 request per sport per day (8 requests/day max) → 24h freeze en contrato
ODDS_MODE_BY_SPORT: Dict[str, Dict[str, str]] = {
    # SportsGameOdds FREE tier (8 deportes soportados)
    "nfl": {"mode": "sportsgameodds", "league_id": "NFL"},
    "nba": {"mode": "sportsgameodds", "league_id": "NBA"},
    "mlb": {"mode": "sportsgameodds", "league_id": "MLB"},
    "nhl": {"mode": "sportsgameodds", "league_id": "NHL"},
    "college_football": {"mode": "sportsgameodds", "league_id": "NCAAF"},
    "college_basketball": {"mode": "sportsgameodds", "league_id": "NCAAB"},
    "soccer_champions": {"mode": "sportsgameodds", "league_id": "UEFA_CHAMPIONS_LEAGUE"},
    "soccer_mls": {"mode": "sportsgameodds", "league_id": "MLS"},
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
    Ingest odds for a day - MIGRATED TO SportsGameOdds.com
    
    Strategy:
    - SportsGameOdds FREE tier: 8 sports, 9 bookmakers, 2,500 objects/month
    - Rate limit: 10 requests/minute, 10 minute update frequency
    - Implementation: 1 request per sport per day = 8 requests/day max
    - Caching: Daily cache ensures contract freeze works (24h, no re-fetch)
    - Sports: NFL, NBA, MLB, NHL, NCAAF, NCAAB, UEFA_CHAMPIONS_LEAGUE, MLS
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
        "strategy": "SPORTSGAMEODDS_8_SPORTS_24H_FREEZE",
        "sports_selected": selected,
        "max_events_per_sport": max_events_per_sport,
        "sports": [],
    }

    # Initialize SportsGameOdds client with caching (FREE tier, 2,500 objects/month, 10 req/min)
    # Caching ensures we fetch all odds ONCE per day (1 request per sport = 8 requests/day max)
    odds_client = SportsGameOddsClient()
    
    # Fetch all odds for the day (uses cache if fresh)
    logger.info(f"Fetching odds for {day} (uses caching, 8 requests/day max for SportsGameOdds)")
    all_odds = odds_client.fetch_all_odds(day, force_refresh=force)
    
    odds_sports_used = []

    for sport in selected:
        conf = ODDS_MODE_BY_SPORT[sport]
        out_file = out_dir / f"{sport}.json"
        
        if out_file.exists() and not force:
            summary["sports"].append(OddsIngestSummary(sport, "skipped", str(out_file), 0, 0).__dict__)
            continue

        try:
            mode = conf.get("mode", "sportsgameodds")
            
            # Use SportsGameOdds for real betting odds (8 leagues with 9 bookmakers each)
            if mode == "sportsgameodds":
                league_id = conf.get("league_id", sport)
                
                # Get raw events from SportsGameOdds cache
                raw_events = all_odds.get(sport, [])
                
                # Transform SportsGameOdds RAW format to normalized format expected by system
                # Input: SportsGameOdds RAW with odds dict and players dict
                # Output: {sport, event_id, response: {response: [{bookmakers: [{name, bets: [{name, values}]}]}]}}
                formatted_events = []
                
                for idx, raw_event in enumerate(raw_events):
                    try:
                        event_id = idx + 1
                        teams = raw_event.get("teams", {})
                        home_team = teams.get("home", {}).get("names", {}).get("short", "HOME")
                        away_team = teams.get("away", {}).get("names", {}).get("short", "AWAY")
                        
                        # Extract odds from SportsGameOdds format
                        odds_dict = raw_event.get("odds", {})
                        bookmakers_data = []
                        
                        # Collect odds by bookmaker
                        bookmaker_bets = {}
                        
                        for odd_id, odd_info in odds_dict.items():
                            # Skip if no odds available
                            if not odd_info.get("bookOddsAvailable") and not odd_info.get("fairOddsAvailable"):
                                continue
                            
                            # Extract market type from oddID
                            # Format examples: "points-home-reg-ml-home", "points-away-1h-ou-over"
                            parts = odd_id.split("-")
                            if len(parts) < 5:
                                continue
                            
                            market_period = parts[2]  # "reg", "1h", "game", etc
                            bet_type = parts[3]        # "ml" (moneyline), "sp" (spread), "ou" (over/under)
                            side = parts[4]            # "home", "away", "over", "under"
                            
                            # Focus on main market moneylines (h2h)
                            if bet_type not in ["ml", "sp", "ou"]:
                                continue
                            
                            # Extract odds by bookmaker
                            by_bookmaker = odd_info.get("byBookmaker", {})
                            
                            for bm_name, bm_data in by_bookmaker.items():
                                odds_value = bm_data.get("odds")
                                if not odds_value:
                                    continue
                                
                                if bm_name not in bookmaker_bets:
                                    bookmaker_bets[bm_name] = {}
                                
                                # Group by market type (h2h, spreads, totals)
                                market_key = bet_type
                                if market_key not in bookmaker_bets[bm_name]:
                                    bookmaker_bets[bm_name][market_key] = []
                                
                                # Create bet value
                                value_entry = {
                                    "value": side,
                                    "odd": _parse_american_odds(odds_value),
                                }
                                
                                # Add point if applicable (for spreads and totals)
                                point = odd_info.get("bookSpread") or odd_info.get("fairSpread")
                                if point:
                                    value_entry["point"] = float(point)
                                
                                bookmaker_bets[bm_name][market_key].append(value_entry)
                        
                        # Format bookmakers for output
                        for bm_name, markets in bookmaker_bets.items():
                            bets_list = []
                            for market_type, values in markets.items():
                                if values:
                                    bets_list.append({
                                        "name": market_type,
                                        "values": values,
                                    })
                            
                            if bets_list:
                                bookmakers_data.append({
                                    "name": bm_name,
                                    "bets": bets_list,
                                })
                        
                        # Create normalized event structure
                        if bookmakers_data:
                            formatted_events.append({
                                "sport": sport,
                                "event_id": event_id,
                                "response": {
                                    "response": [
                                        {
                                            "bookmakers": bookmakers_data,
                                        }
                                    ]
                                }
                            })
                    
                    except Exception as e:
                        logger.debug(f"Error processing event in {sport}: {e}")
                        continue
                
                if formatted_events:
                    out_file.write_text(json.dumps(formatted_events, ensure_ascii=False, indent=2), encoding="utf-8")
                    summary["sports"].append(OddsIngestSummary(sport, "created", str(out_file), 1, len(formatted_events)).__dict__)
                    odds_sports_used.append(sport)
                else:
                    summary["sports"].append(OddsIngestSummary(sport, "no_odds", str(out_file), 0, 0).__dict__)
                continue


        except Exception as e:
            logger.error(f"Error processing {sport}: {e}")
            summary["sports"].append(OddsIngestSummary(sport, "error", str(out_file), 0, 0).__dict__)

    # Log summary
    summary["sportsgameodds_sports_used"] = odds_sports_used
    summary["sports_count"] = len(odds_sports_used)
    summary["note"] = "Odds fetched once per day and cached (8 requests/day max for SportsGameOdds FREE tier)"

    return summary


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest odds multisport into api/data/odds/<day>/<sport>.json")
    p.add_argument("day", nargs="?", default=None, help="YYYY-MM-DD (default: today)")
    p.add_argument("--day", dest="day_opt", default=None, help="YYYY-MM-DD (alias; optional named)")
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
    day = args.day_opt or args.day
    sports = [s.strip() for s in args.sports.split(',') if s.strip()] if args.sports else None
    summary = ingest_odds_for_day(
        day=day,
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
