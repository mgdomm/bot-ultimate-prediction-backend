from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _odds_dir(day: str) -> Path:
    return _repo_root() / "api" / "data" / "odds" / day


def _safe_load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def _market_key(market: str) -> str:
    m = _norm(market)
    if m in {"ou", "o/u", "over/under", "goals over/under", "total"}:
        return "ou"
    if m in {"sp", "spread", "handicap", "asian handicap", "asian handicap (reg time)"}:
        return "sp"
    return m


def build_point_index(day: str) -> Dict[Tuple[str, str, str, str], float]:
    """
    Lee api/data/odds/<day>/*.json y construye un índice:
      (sport, event_id, market_key, selection) -> point/total (float)
    Solo guarda valores numéricos.
    """
    odds_path = _odds_dir(day)
    if not odds_path.exists():
        return {}

    out: Dict[Tuple[str, str, str, str], float] = {}
    for file in odds_path.glob("*.json"):
        data = _safe_load(file)
        if not isinstance(data, list):
            continue
        for item in data:
            if not isinstance(item, dict):
                continue
            sport = _norm(item.get("sport"))
            event_id = _norm(item.get("event_id") or item.get("eventId"))
            if not sport or not event_id:
                continue

            resp = item.get("response")
            if not isinstance(resp, dict):
                continue
            arr = resp.get("response")
            if not isinstance(arr, list):
                continue

            for bet_container in arr:
                if not isinstance(bet_container, dict):
                    continue
                bookmakers = bet_container.get("bookmakers")
                if not isinstance(bookmakers, list):
                    continue
                for bm in bookmakers:
                    if not isinstance(bm, dict):
                        continue
                    bets = bm.get("bets")
                    if not isinstance(bets, list):
                        continue
                    for bet in bets:
                        if not isinstance(bet, dict):
                            continue
                        mk = _market_key(bet.get("name"))
                        values = bet.get("values")
                        if not isinstance(values, list):
                            continue
                        for val in values:
                            if not isinstance(val, dict):
                                continue
                            sel = _norm(val.get("value"))
                            point = val.get("point")
                            total = val.get("total")
                            num = None
                            for candidate in (point, total):
                                try:
                                    if candidate is None:
                                        continue
                                    f = float(candidate)
                                    if f == f:  # not NaN
                                        num = f
                                        break
                                except Exception:
                                    continue
                            if num is None:
                                continue
                            out[(sport, event_id, mk, sel)] = num
    return out


def inject_lines_into_contract(contract: Dict[str, Any], day: str) -> None:
    """
    Añade `line` a picks cuando exista en odds raw (point/total) para el mercado/selección.
    No persiste en disco; se usa en memoria al servir /bets/today.
    """
    idx = build_point_index(day)
    if not idx:
        return

    def _enrich_pick(pick: Dict[str, Any]):
        if not isinstance(pick, dict):
            return
        if pick.get("line") is not None:
            return
        sport = _norm(pick.get("sport"))
        eid = _norm(pick.get("eventId"))
        mk = _market_key(pick.get("market"))
        sel = _norm(pick.get("selection"))
        if not sport or not eid or not mk or not sel:
            return
        val = idx.get((sport, eid, mk, sel))
        if val is not None:
            pick["line"] = val

    def _iter_picks(c: Dict[str, Any]):
        pc = c.get("picks_classic") or []
        for container in pc:
            if isinstance(container, list):
                for pick in container:
                    yield pick
            elif isinstance(container, dict):
                yield container
        pbs = c.get("picks_by_sport") or {}
        if isinstance(pbs, dict):
            for picks in pbs.values():
                if isinstance(picks, list):
                    for pick in picks:
                        yield pick
        pp = c.get("picks_parlay_premium") or []
        if isinstance(pp, list):
            for par in pp:
                if not isinstance(par, dict):
                    continue
                legs = par.get("legs") or par.get("picks")
                if isinstance(legs, list):
                    for leg in legs:
                        yield leg
        feat = c.get("daily_featured_parlay")
        if isinstance(feat, dict):
            legs = feat.get("legs") or feat.get("picks")
            if isinstance(legs, list):
                for leg in legs:
                    yield leg

    for pk in _iter_picks(contract):
        _enrich_pick(pk)
