from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"

MAX_PICKS = 10

# Regla económica (misma idea que picks_parlay.py)
PROB_FLOOR = 0.40
VALUE_MARGIN = 0.03
FALLBACK_VALUE_MARGIN = 0.027


def _f(x: Any, default: float = float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _s(x: Any) -> str:
    return "" if x is None else str(x)


def _key(x: Dict[str, Any]) -> Tuple[str, str, str, str]:
    return (_s(x.get("sport")), _s(x.get("eventId")), _s(x.get("market")), _s(x.get("selection")))


def _p_implied(odds: float) -> float:
    return 1.0 / odds if odds > 0 else float("nan")


def load_pool(day: str, name: str) -> List[Dict[str, Any]]:
    p = API_DATA_DIR / "pools" / day / f"{name}.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def as_pick(x: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # pools/inflated.json ya trae: sport,eventId,market,selection,odds,probability,edge,consensus,marketType,marketRisk,inflated
    sport = _s(x.get("sport")).strip()
    event_id = _s(x.get("eventId")).strip()
    market = x.get("market")
    selection = x.get("selection")
    odds = _f(x.get("odds"))
    p_est = _f(x.get("probability"))
    edge = _f(x.get("edge"), default=0.0)

    if not sport or not event_id or market is None or selection is None:
        return None
    if odds != odds or odds <= 1.01:
        return None
    if p_est != p_est:
        return None

    p_impl = _p_implied(float(odds))
    if p_impl != p_impl:
        return None

    return {
        "sport": sport,
        "eventId": event_id,
        "market": market,
        "selection": selection,
        "odds": round(float(odds), 2),
        "p_implied": round(float(p_impl), 4),
        "p_estimated": round(float(p_est), 4),
        "edge": round(float(edge), 4),
        "consensus": x.get("consensus"),
        "marketType": x.get("marketType"),
        "marketRisk": x.get("marketRisk"),
        "inflated": bool(x.get("inflated", False)),
        "type": "VALUE_SINGLE",
    }


def passes_value_rule(pick: Dict[str, Any], margin: float) -> bool:
    odds = _f(pick.get("odds"))
    p_est = _f(pick.get("p_estimated"))
    if odds != odds or p_est != p_est or odds <= 1.01:
        return False
    min_required = max(float(PROB_FLOOR), (1.0 / float(odds)) + float(margin))
    return float(p_est) >= float(min_required)


def build_value_picks(day: str) -> List[Dict[str, Any]]:
    inflated = load_pool(day, "inflated")
    eligible = load_pool(day, "parlay_eligible")

    raw = inflated + eligible

    picks: List[Dict[str, Any]] = []
    seen = set()

    for x in raw:
        if not isinstance(x, dict):
            continue
        p = as_pick(x)
        if not p:
            continue
        k = _key(p)
        if k in seen:
            continue
        seen.add(k)
        picks.append(p)

    # Preferimos inflated=True y mayor edge, luego mayor p_estimated, luego odds más baja (más “safe” dentro de value)
    picks.sort(key=lambda r: (
        1 if r.get("inflated") else 0,
        _f(r.get("edge"), default=-1e9),
        _f(r.get("p_estimated"), default=-1e9),
        -_f(r.get("odds"), default=999.0),
        _key(r),
    ), reverse=True)

    # 1) premium margin
    out = [p for p in picks if passes_value_rule(p, VALUE_MARGIN)]

    # 2) fallback margin si no hay suficientes
    if len(out) < MAX_PICKS:
        out2 = [p for p in picks if passes_value_rule(p, FALLBACK_VALUE_MARGIN)]
        # merge sin dups preservando orden
        merged: List[Dict[str, Any]] = []
        seen2 = set()
        for z in out + out2:
            k = _key(z)
            if k in seen2:
                continue
            seen2.add(k)
            merged.append(z)
        out = merged

    return out[:MAX_PICKS]


def run_for_day(day: Optional[str] = None) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    out_dir = API_DATA_DIR / "picks_value" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "all.json"

    picks = build_value_picks(day)
    out_file.write_text(json.dumps(picks, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"day": day, "picks": len(picks), "output": str(out_file)}


if __name__ == "__main__":
    print(json.dumps(run_for_day(), ensure_ascii=False, indent=2))
