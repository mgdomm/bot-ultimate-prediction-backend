from __future__ import annotations

import argparse
import json
from datetime import date
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"

SIMPLE_MARKETS = {"over/under", "moneyline", "handicap"}

# Reglas producto (ajustadas a datos reales: hoy no hay LOW)
SAFE_P_MIN = 0.68
SAFE_EV_MIN = 0.0
SAFE_ALLOWED_RISK = {"MEDIUM", "HIGH"}

BOOM_P_MIN = 0.64
BOOM_EV_MIN = 0.0
BOOM_ALLOWED_RISK = {"MEDIUM", "HIGH"}

BOOM_TARGET_ODDS_1 = 3.0
BOOM_TARGET_ODDS_2 = 2.5

OUTPUT_FILENAMES = {
    "SAFE_2_A": "parlay_safe_2_a.json",
    "SAFE_2_B": "parlay_safe_2_b.json",
    "SAFE_4": "parlay_safe_4.json",
    "BOOM_3": "parlay_boom_3.json",
}

AGGREGATE_FILENAME = "parlays.json"


def _f(x: Any, default: float = -1e9) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _s(x: Any) -> str:
    return "" if x is None else str(x)


def _risk_level(p: Dict[str, Any]) -> str:
    return str(((p.get("risk") or {}).get("level") or "")).upper()


def _market_key(p: Dict[str, Any]) -> str:
    return str((p.get("market") or "")).lower()


def _is_simple_market(p: Dict[str, Any]) -> bool:
    return _market_key(p) in SIMPLE_MARKETS


def _event_key(p: Dict[str, Any]) -> Tuple[str, str]:
    return (_s(p.get("sport")), _s(p.get("eventId")))


def _pick_key(p: Dict[str, Any]) -> Tuple[str, str, str, str]:
    return (_s(p.get("sport")), _s(p.get("eventId")), _s(p.get("market")), _s(p.get("selection")))


def _prob(p: Dict[str, Any]) -> float:
    return _f(p.get("p_estimated"), default=0.0)


def _ev(p: Dict[str, Any]) -> float:
    return _f(p.get("ev"), default=-1e9)


def _odds(p: Dict[str, Any]) -> float:
    return _f(p.get("odds"), default=1.0)


def _best_pick_per_event(picks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Escoge 1 pick por evento. Criterio: prob desc, ev desc, odds desc
    """
    best: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for p in picks:
        ek = _event_key(p)
        cur = best.get(ek)
        if cur is None:
            best[ek] = p
            continue
        a = (_prob(cur), _ev(cur), _odds(cur))
        b = (_prob(p), _ev(p), _odds(p))
        if b > a:
            best[ek] = p
    return list(best.values())


def _dedupe_exact(picks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Dedupe por (sport,eventId,market,selection) quedándote el mejor EV.
    """
    best: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    for p in picks:
        k = _pick_key(p)
        cur = best.get(k)
        if cur is None or _ev(p) > _ev(cur):
            best[k] = p
    return list(best.values())


def combined_odds(legs: List[Dict[str, Any]]) -> float:
    out = 1.0
    for p in legs:
        out *= _odds(p)
    return out


def combined_prob(legs: List[Dict[str, Any]]) -> float:
    out = 1.0
    for p in legs:
        out *= _prob(p)
    return out


def make_parlay(kind: str, legs: List[Dict[str, Any]], label: str, note: Optional[str] = None) -> Dict[str, Any]:
    payload = {
        "type": "PARLAY_PREMIUM",
        "kind": kind,            # SAFE_2 / SAFE_4 / BOOM_3
        "label": label,          # texto para UI
        "legs": legs,            # lo que hay que marcar
        "combined_odds": round(combined_odds(legs), 4),
        "prob_parlay": round(combined_prob(legs), 4),
    }
    if note:
        payload["note"] = note
    return payload


def filter_pool(all_picks: List[Dict[str, Any]], pmin: float, evmin: float, allowed_risks: set[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in all_picks:
        if not _is_simple_market(p):
            continue
        if _risk_level(p) not in allowed_risks:
            continue
        if _prob(p) < pmin:
            continue
        if _ev(p) < evmin:
            continue
        if not _s(p.get("sport")) or not _s(p.get("eventId")):
            continue
        out.append(p)
    return out


def build_safe_parlays(all_picks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pool = filter_pool(all_picks, SAFE_P_MIN, SAFE_EV_MIN, SAFE_ALLOWED_RISK)
    pool = _dedupe_exact(pool)
    per_event = _best_pick_per_event(pool)

    per_event.sort(key=lambda p: (_prob(p), _ev(p), _odds(p)), reverse=True)

    used_events: set[Tuple[str, str]] = set()

    def take_distinct(n: int) -> List[Dict[str, Any]]:
        chosen: List[Dict[str, Any]] = []
        for p in per_event:
            ek = _event_key(p)
            if ek in used_events:
                continue
            chosen.append(p)
            used_events.add(ek)
            if len(chosen) >= n:
                break
        if len(chosen) < n:
            for p in per_event:
                ek = _event_key(p)
                if ek in {_event_key(x) for x in chosen}:
                    continue
                chosen.append(p)
                if len(chosen) >= n:
                    break
        return chosen

    safe2_a_legs = take_distinct(2)
    safe2_b_legs = take_distinct(2)
    safe4_legs = take_distinct(4)

    out: List[Dict[str, Any]] = []
    if len(safe2_a_legs) == 2:
        out.append(make_parlay("SAFE_2", safe2_a_legs, "Seguro (2 piernas)"))
    if len(safe2_b_legs) == 2:
        out.append(make_parlay("SAFE_2", safe2_b_legs, "Seguro (2 piernas)"))
    if len(safe4_legs) == 4:
        out.append(make_parlay("SAFE_4", safe4_legs, "Seguro (4 piernas)"))

    return out


def _diversity_markets_ok(legs: List[Dict[str, Any]]) -> bool:
    markets = {_market_key(p) for p in legs}
    return len(markets) >= 2


def _diversity_sports_ok(legs: List[Dict[str, Any]]) -> bool:
    sports = {_s(p.get("sport")).lower() for p in legs}
    return len(sports) >= 2


def build_boom_parlay(all_picks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    pool = filter_pool(all_picks, BOOM_P_MIN, BOOM_EV_MIN, BOOM_ALLOWED_RISK)
    pool = _dedupe_exact(pool)

    per_event = _best_pick_per_event(pool)
    per_event.sort(key=lambda p: (_prob(p), _ev(p), _odds(p)), reverse=True)

    K = min(60, len(per_event))
    candidates = per_event[:K]
    if len(candidates) < 3:
        return None

    def search(target_odds: float, diversity_mode: str) -> Optional[List[Dict[str, Any]]]:
        best_local: Optional[List[Dict[str, Any]]] = None
        best_score: Tuple[float, float] = (-1.0, -1.0)  # (prob, odds)

        for a, b, c in combinations(candidates, 3):
            legs = [a, b, c]
            if len({_event_key(x) for x in legs}) != 3:
                continue

            if diversity_mode == "markets":
                if not _diversity_markets_ok(legs):
                    continue
            elif diversity_mode == "sports":
                if not _diversity_sports_ok(legs):
                    continue

            o = combined_odds(legs)
            if o < target_odds:
                continue
            pr = combined_prob(legs)
            score = (pr, o)
            if score > best_score:
                best_score = score
                best_local = legs

        return best_local

    legs = search(BOOM_TARGET_ODDS_1, "markets") or search(BOOM_TARGET_ODDS_2, "markets")
    if legs:
        return make_parlay("BOOM_3", legs, "Boom (3 piernas)")

    legs = search(BOOM_TARGET_ODDS_1, "sports") or search(BOOM_TARGET_ODDS_2, "sports")
    if legs:
        return make_parlay("BOOM_3", legs, "Boom (3 piernas)", note="Fallback: mismo mercado, variedad por deporte")

    # 3) Último fallback: mejor por probabilidad
    best_local = None
    best_score = (-1.0, -1.0)
    for a, b, c in combinations(candidates, 3):
        legs = [a, b, c]
        if len({_event_key(x) for x in legs}) != 3:
            continue
        if not _diversity_sports_ok(legs):
            continue
        pr = combined_prob(legs)
        o = combined_odds(legs)
        score = (pr, o)
        if score > best_score:
            best_score = score
            best_local = legs
    if best_local:
        return make_parlay("BOOM_3", best_local, "Boom (3 piernas)", note="Fallback final: mejor probabilidad")

    best_local = None
    best_score = (-1.0, -1.0)
    for a, b, c in combinations(candidates, 3):
        legs = [a, b, c]
        if len({_event_key(x) for x in legs}) != 3:
            continue
        pr = combined_prob(legs)
        o = combined_odds(legs)
        score = (pr, o)
        if score > best_score:
            best_score = score
            best_local = legs
    if best_local:
        return make_parlay("BOOM_3", best_local, "Boom (3 piernas)", note="Fallback final: sin diversidad disponible")

    return None


def run_for_day(day: Optional[str] = None) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    in_path = API_DATA_DIR / "odds_premium" / day / "all.json"
    if not in_path.exists():
        raise FileNotFoundError(f"No existe odds_premium: {in_path}")

    all_picks = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(all_picks, list):
        raise ValueError("odds_premium/all.json no es una lista")

    safe = build_safe_parlays(all_picks)
    boom = build_boom_parlay(all_picks)

    out_dir = API_DATA_DIR / "picks_parlay" / day
    out_dir.mkdir(parents=True, exist_ok=True)

    written: List[str] = []

    safe_items = [p for p in safe if p.get("kind") in {"SAFE_2", "SAFE_4"}]
    safe_items.sort(key=lambda x: (0 if x.get("kind") == "SAFE_2" else 1, x.get("label", "")))

    out_map: List[Tuple[str, Dict[str, Any]]] = []
    safe2 = [x for x in safe_items if x.get("kind") == "SAFE_2"][:2]
    if len(safe2) > 0:
        out_map.append((OUTPUT_FILENAMES["SAFE_2_A"], safe2[0]))
    if len(safe2) > 1:
        out_map.append((OUTPUT_FILENAMES["SAFE_2_B"], safe2[1]))
    safe4 = [x for x in safe_items if x.get("kind") == "SAFE_4"][:1]
    if safe4:
        out_map.append((OUTPUT_FILENAMES["SAFE_4"], safe4[0]))

    aggregate: List[Dict[str, Any]] = []

    for fname, payload in out_map:
        (out_dir / fname).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(out_dir / fname))
        aggregate.append(payload)

    if boom is not None:
        (out_dir / OUTPUT_FILENAMES["BOOM_3"]).write_text(json.dumps(boom, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(out_dir / OUTPUT_FILENAMES["BOOM_3"]))
        aggregate.append(boom)

        feat_dir = API_DATA_DIR / "picks_parlay_featured" / day
        feat_dir.mkdir(parents=True, exist_ok=True)
        (feat_dir / "featured_parlay.json").write_text(json.dumps(boom, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(feat_dir / "featured_parlay.json"))

    # IMPORTANT: agregador esperado por pipeline/contract
    agg_path = out_dir / AGGREGATE_FILENAME
    agg_path.write_text(json.dumps({"parlays": aggregate}, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(str(agg_path))

    return {
        "day": day,
        "safe_count": len(safe_items),
        "boom_generated": boom is not None,
        "parlays_aggregate_count": len(aggregate),
        "written": written,
    }


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build premium parlays from api/data/odds_premium/<day>/all.json")
    p.add_argument("day", nargs="?", default=None, help="YYYY-MM-DD (default: today)")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    print(json.dumps(run_for_day(args.day), ensure_ascii=False, indent=2))
