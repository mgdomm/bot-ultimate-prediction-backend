from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from services.api_sports_client import ApiSportsClient
except ModuleNotFoundError:
    from api.services.api_sports_client import ApiSportsClient  # type: ignore

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"

# Para FREE: límite determinista de requests por deporte
MAX_EVENTS_PER_SPORT_DEFAULT = 40

# Estrategia odds por deporte (según evidencia 2026-01-17)
ODDS_MODE_BY_SPORT: Dict[str, Dict[str, str]] = {
    "football": {"mode": "date"},
    # Odds por evento con param "game"
    "basketball": {"mode": "per_event", "param": "game"},
    "baseball": {"mode": "per_event", "param": "game"},
    "hockey": {"mode": "per_event", "param": "game"},
    "handball": {"mode": "per_event", "param": "game"},
    "volleyball": {"mode": "per_event", "param": "game"},
    "rugby": {"mode": "per_event", "param": "game"},
    "afl": {"mode": "per_event", "param": "game"},
    "nfl": {"mode": "per_event", "param": "game"},
    # Deshabilitados por evidencia (/odds no existe):
    # "nba": ...
    # "formula-1": ...
}

@dataclass(frozen=True)
class OddsIngestSummary:
    sport: str
    status: str  # created | skipped
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


def _load_event_ids(day: str, sport: str) -> List[int]:
    p = API_DATA_DIR / "events" / day / f"{sport}.json"
    if not p.exists():
        return []
    payload = json.loads(p.read_text(encoding="utf-8"))
    ids: List[int] = []
    for item in _first_list(payload):
        eid = _extract_event_id(sport, item)
        if eid is not None:
            ids.append(eid)
    return sorted(set(ids))


def ingest_odds_for_day(
    day: Optional[str] = None,
    force: bool = False,
    sports: Optional[List[str]] = None,
    max_events_per_sport: int = MAX_EVENTS_PER_SPORT_DEFAULT,
) -> Dict[str, Any]:
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
        "sports_selected": selected,
        "max_events_per_sport": max_events_per_sport,
        "sports": [],
    }

    for sport in selected:
        conf = ODDS_MODE_BY_SPORT[sport]
        mode = conf["mode"]

        out_file = out_dir / f"{sport}.json"
        if out_file.exists() and not force:
            summary["sports"].append(OddsIngestSummary(sport, "skipped", str(out_file), 0, 0).__dict__)
            continue

        client = ApiSportsClient(sport)

        if mode == "date":
            payload = client.get("/odds", params={"date": day})
            out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            nz = int(payload.get("results") or 0)
            summary["sports"].append(OddsIngestSummary(sport, "created", str(out_file), 1, nz).__dict__)
            continue

        # per_event
        param = conf["param"]
        ids = _load_event_ids(day, sport)[:max_events_per_sport]

        blocks: List[Dict[str, Any]] = []
        nonzero = 0

        for eid in ids:
            payload = client.get("/odds", params={param: eid})
            r = int(payload.get("results") or 0)
            if r > 0:
                nonzero += 1
            blocks.append(
                {"sport": sport, "event_id": eid, "param": param, "results": r, "response": payload}
            )

        out_file.write_text(json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8")
        summary["sports"].append(OddsIngestSummary(sport, "created", str(out_file), len(ids), nonzero).__dict__)

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
    sports = [s.strip() for s in args.sports.split(",") if s.strip()] if args.sports else None
    print(
        json.dumps(
            ingest_odds_for_day(
                day=args.day,
                force=bool(args.force),
                sports=sports,
                max_events_per_sport=int(args.max_events),
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
