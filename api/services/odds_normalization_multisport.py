from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def _as_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _football_date_dict_to_payloads(sport: str, data: Dict[str, Any]) -> List[Tuple[str, int, Dict[str, Any]]]:
    """
    Football en modo "date" guarda el JSON directo del endpoint:
      {"response":[{"fixture":{"id":...}, "bookmakers":[...], ...}, ...], ...}

    Para reutilizar el normalizador actual (que espera payload["response"] como lista),
    generamos 1 payload por evento: {"response":[item]} y event_id = fixture.id
    """
    out: List[Tuple[str, int, Dict[str, Any]]] = []
    resp = data.get("response")
    if not isinstance(resp, list):
        return out

    for item in resp:
        if not isinstance(item, dict):
            continue
        fixture = item.get("fixture")
        if not isinstance(fixture, dict):
            continue
        fid = fixture.get("id")
        if fid is None:
            continue
        try:
            event_id = int(fid)
        except Exception:
            continue

        out.append((sport, event_id, {"response": [item]}))

    return out


def _iter_odds_payloads_for_sport(day: str, sport: str) -> List[Tuple[str, int, Dict[str, Any]]]:
    """
    Devuelve lista de tuples: (sport, event_id, payload_dict)
    donde payload_dict es un dict con clave "response": [ ... items ... ]
    """
    p = API_DATA_DIR / "odds" / day / f"{sport}.json"
    if not p.exists():
        return []

    data = json.loads(p.read_text(encoding="utf-8"))
    out: List[Tuple[str, int, Dict[str, Any]]] = []

    # ✅ football (date mode) actual: dict directo con response:[{fixture:{id},bookmakers...}, ...]
    if sport == "football" and isinstance(data, dict):
        return _football_date_dict_to_payloads(sport, data)

    # A partir de aquí esperamos lista (per_event blocks)
    if not isinstance(data, list):
        return out

    # football legacy format: [{fixture:<id>, response:<payload>}]
    if (
        sport == "football"
        and data
        and isinstance(data[0], dict)
        and "fixture" in data[0]
        and "response" in data[0]
    ):
        for block in data:
            eid = block.get("fixture")
            payload = block.get("response")
            if eid is None or not isinstance(payload, dict):
                continue
            try:
                out.append((sport, int(eid), payload))
            except Exception:
                continue
        return out

    # multisport format: [{sport,event_id,param,results,response:<payload>}]
    for block in data:
        if not isinstance(block, dict):
            continue
        eid = block.get("event_id")
        payload = block.get("response")
        if eid is None or not isinstance(payload, dict):
            continue
        try:
            out.append((sport, int(eid), payload))
        except Exception:
            continue

    return out


def normalize_odds_for_day(day: Optional[str] = None) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    out_dir = API_DATA_DIR / "odds_normalized" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "all.json"

    odds_dir = API_DATA_DIR / "odds" / day
    sports = sorted([p.stem for p in odds_dir.glob("*.json")])

    normalized: List[Dict[str, Any]] = []
    sport_counts: Dict[str, int] = {}

    for sport in sports:
        payloads = _iter_odds_payloads_for_sport(day, sport)
        sport_total = 0

        for _sport, event_id, payload in payloads:
            for item in payload.get("response", []) or []:
                bookmakers = item.get("bookmakers") or []
                for bookmaker in bookmakers:
                    bookmaker_name = bookmaker.get("name")
                    bets = bookmaker.get("bets") or []
                    for bet in bets:
                        market = bet.get("name")
                        values = bet.get("values") or []
                        for value in values:
                            odds = _as_float(value.get("odd"))
                            selection = value.get("value")
                            if odds is None or selection is None or market is None:
                                continue

                            normalized.append(
                                {
                                    "sport": sport,
                                    "eventId": str(event_id),
                                    "bookmaker": bookmaker_name,
                                    "market": market,
                                    "selection": selection,
                                    "odds": odds,
                                }
                            )
                            sport_total += 1

        sport_counts[sport] = sport_total

    normalized.sort(
        key=lambda r: (
            r.get("sport") or "",
            int(r.get("eventId") or 0),
            r.get("market") or "",
            str(r.get("selection") or ""),
            r.get("bookmaker") or "",
            float(r.get("odds") or 0.0),
        )
    )

    out_file.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "day": day,
        "sports": sports,
        "records": len(normalized),
        "by_sport": sport_counts,
        "file": str(out_file),
    }


if __name__ == "__main__":
    print(json.dumps(normalize_odds_for_day(), ensure_ascii=False, indent=2))
