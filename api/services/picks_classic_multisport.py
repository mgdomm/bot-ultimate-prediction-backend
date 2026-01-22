from __future__ import annotations

import os
import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter, defaultdict

MAX_PICKS = 10

# Probabilidad conservadora (seguridad = probabilidad de acertar)
SHRINK_W = 0.35  # peso del modelo; (1-w) = peso del mercado

# Rangos “seguros” para principiantes
ODDS_MIN = 1.20
ODDS_MAX = 1.80

# Umbral principal (con fallback si un día viene flojo)
P_SAFE_MIN_PRIMARY = 0.70
P_SAFE_MIN_FALLBACK = 0.68


# Mercados que consideramos “modernos y razonables” (evitar exóticos tipo correct score / goleadores)
STANDARD_MARKETS = {
    "over/under",
    "goals over/under",  # alias común en API-SPORTS (equivalente a over/under)
    "over/under 1st half",
    "over/under (reg time)",
    "asian handicap",
    "asian handicap first half",
    "asian handicap (reg time)",
    "total - home",
    "total - away",
    "home/away",
    "3way result",
    "moneyline",
    "handicap",
}

# Para que Classic no sea repetitivo: límite por mercado en el top 10
MAX_PER_MARKET = {
    "over/under": 4,
    "asian handicap": 3,
    "total - home": 2,
    "total - away": 2,
    # el resto: por defecto 2
}
DEFAULT_MAX_PER_MARKET = 2

# Defaults for economic rule (aligned with picks_parlay.py guardrails)
try:
    from api.services.picks_parlay import PARLAY_GUARDRAILS  # type: ignore
except ModuleNotFoundError:
    from services.picks_parlay import PARLAY_GUARDRAILS  # type: ignore

_GUARD = (PARLAY_GUARDRAILS or {}).get("principal_2_legs", {}) if isinstance(PARLAY_GUARDRAILS, dict) else {}
_DEFAULT_CLASSIC_PROB_FLOOR = float(_GUARD.get("min_combined_probability_floor", 0.40))
_DEFAULT_CLASSIC_VALUE_MARGIN = float(_GUARD.get("value_margin", 0.03))

# Allow override via env vars (strings)
CLASSIC_PROB_FLOOR = float(os.environ.get("CLASSIC_PROB_FLOOR", str(_DEFAULT_CLASSIC_PROB_FLOOR)))
CLASSIC_VALUE_MARGIN = float(os.environ.get("CLASSIC_VALUE_MARGIN", str(_DEFAULT_CLASSIC_VALUE_MARGIN)))

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def _f(x: Any, default: float = float("nan")) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _s(x: Any) -> str:
    return "" if x is None else str(x)


def _market(sel: Dict[str, Any]) -> str:
    return str(sel.get("market") or "").lower().strip()


def p_safe(sel: Dict[str, Any]) -> float:
    pe = _f(sel.get("p_estimated"))
    pi = _f(sel.get("p_implied"))
    if pe != pe or pi != pi:  # NaN check
        return float("nan")
    return SHRINK_W * pe + (1.0 - SHRINK_W) * pi


def market_cap(mkt: str) -> int:
    return MAX_PER_MARKET.get(mkt, DEFAULT_MAX_PER_MARKET)


def is_candidate(sel: Dict[str, Any], pmin: float) -> bool:
    mkt = _market(sel)
    if mkt not in STANDARD_MARKETS:
        return False

    odds = _f(sel.get("odds"))
    if odds != odds:
        return False
    if odds < ODDS_MIN or odds > ODDS_MAX:
        return False

    ps = p_safe(sel)
    if ps != ps:
        return False
    if ps < pmin:
        return False

    # Regla económica (alineada con picks_parlay.py):
    # p_estimated debe superar la probabilidad implícita + margen, con piso duro.
    pe = _f(sel.get("p_estimated"))
    if pe != pe:
        return False
    min_required = max(float(CLASSIC_PROB_FLOOR), (1.0 / float(odds)) + float(CLASSIC_VALUE_MARGIN))
    if float(pe) < float(min_required):
        return False

    # Necesitamos evento y deporte sí o sí
    if not _s(sel.get("sport")) or not _s(sel.get("eventId")):
        return False

    return True


def event_key(sel: Dict[str, Any]) -> Tuple[str, str]:
    return (_s(sel.get("sport")), _s(sel.get("eventId")))


def pick_key(sel: Dict[str, Any]) -> Tuple[str, str, str, str]:
    return (_s(sel.get("sport")), _s(sel.get("eventId")), _s(sel.get("market")), _s(sel.get("selection")))


def score(sel: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Orden “inteligente” para seguridad:
    1) p_safe desc
    2) p_estimated desc (si empata)
    3) odds asc (preferimos cuotas más bajas para “seguro”)
    """
    ps = p_safe(sel)
    pe = _f(sel.get("p_estimated"), default=0.0)
    odds = _f(sel.get("odds"), default=999.0)
    return (ps, pe, -odds)


def dedupe_exact(selections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    for sel in selections:
        k = pick_key(sel)
        cur = best.get(k)
        if cur is None or score(sel) > score(cur):
            best[k] = sel
    return list(best.values())


def best_per_event(selections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for sel in selections:
        k = event_key(sel)
        cur = best.get(k)
        if cur is None or score(sel) > score(cur):
            best[k] = sel
    return list(best.values())



def classic_risk_from_p_safe(ps: float) -> Dict[str, Any]:
    """
    Classic se prioriza por probabilidad (p_safe). El 'risk' visible debe reflejar eso.
    Eliminamos EXTREME (venía upstream) y lo mapeamos a LOW/MEDIUM/HIGH.
    """
    if ps >= 0.75:
        level = "LOW"
    elif ps >= 0.60:
        level = "MEDIUM"
    else:
        level = "HIGH"
    return {"level": level}


def build_picks(day: str) -> List[Dict[str, Any]]:
    in_path = API_DATA_DIR / "odds_premium" / day / "all.json"
    if not in_path.exists():
        raise FileNotFoundError(f"No premium odds file found: {in_path}")

    all_sel = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(all_sel, list):
        raise ValueError("odds_premium/all.json no es una lista")

    # 1) Filtrado principal
    cand = [s for s in all_sel if is_candidate(s, P_SAFE_MIN_PRIMARY)]
    cand = dedupe_exact(cand)

    # 2) Fallback si no llegamos
    if len(cand) < MAX_PICKS:
        cand_fb = [s for s in all_sel if is_candidate(s, P_SAFE_MIN_FALLBACK)]
        cand_fb = dedupe_exact(cand_fb)
        cand = cand_fb

    # 3) 1 pick por evento (para que la app no parezca “mismo partido repetido”)
    per_event = best_per_event(cand)

    # 4) Orden por seguridad
    per_event.sort(key=score, reverse=True)

    # 5) Selección con caps por mercado (variedad)
    picked: List[Dict[str, Any]] = []
    used_events: set[Tuple[str, str]] = set()
    market_counts: Counter[str] = Counter()

    for sel in per_event:
        if len(picked) >= MAX_PICKS:
            break
        ek = event_key(sel)
        if ek in used_events:
            continue
        mkt = _market(sel)
        if market_counts[mkt] >= market_cap(mkt):
            continue

        picked.append(sel)
        used_events.add(ek)
        market_counts[mkt] += 1

    # 6) Si por caps no llegamos a 10, rellenamos ignorando caps (pero siempre 1 por evento)
    if len(picked) < MAX_PICKS:
        for sel in per_event:
            if len(picked) >= MAX_PICKS:
                break
            ek = event_key(sel)
            if ek in used_events:
                continue
            picked.append(sel)
            used_events.add(ek)

    # 7) Formato “pick” (mantiene compatibilidad con frontend)
    out: List[Dict[str, Any]] = []
    for sel in picked[:MAX_PICKS]:
        ps = p_safe(sel)
        out.append(
            {
                "sport": sel.get("sport"),
                "eventId": str(sel.get("eventId")),
                "bookmaker": sel.get("bookmaker"),
                "market": sel.get("market"),
                "selection": sel.get("selection"),
                "odds": float(sel.get("odds")),
                "p_implied": float(sel.get("p_implied")),
                "p_estimated": float(sel.get("p_estimated")),
                "p_safe": round(float(ps), 4),
                # EV lo dejamos si existe (útil para el equipo, aunque no gobierna Classic)
                "stake": float(sel.get("stake", 50)),
                "ev": float(sel.get("ev", 0.0)),
                "risk": classic_risk_from_p_safe(ps),
                "premium": bool(sel.get("premium", False)),
                "premium_reason": sel.get("premium_reason"),
            }
        )

    return out


def run_for_day(day: Optional[str] = None) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    out_dir = API_DATA_DIR / "picks_classic" / day
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "all.json"

    picks = build_picks(day)
    out_file.write_text(json.dumps(picks, ensure_ascii=False, indent=2), encoding="utf-8")

    markets = Counter((p.get("market") or "").lower() for p in picks)
    sports = sorted({p.get("sport") for p in picks if p.get("sport")})
    return {
        "day": day,
        "picks": len(picks),
        "sports": sports,
        "markets_top": markets.most_common(10),
        "output": str(out_file),
    }


if __name__ == "__main__":
    print(json.dumps(run_for_day(), ensure_ascii=False, indent=2))
