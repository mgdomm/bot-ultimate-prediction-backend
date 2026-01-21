import json
import os
import statistics
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from api.utils.paths import data_path, ensure_dir


# -------------------------
# Config base (global)
# -------------------------
ODDS_MIN = 1.80

# Umbrales por riesgo estructural del market
THRESHOLDS = {
    # mercados líquidos/binarios o relativamente estables
    "low": {
        "min_books": 6,
        "max_best_vs_2nd": 1.05,
        "min_best_vs_median": 1.03,
    },
    # mercados OK pero con más varianza o menos liquidez
    "medium": {
        "min_books": 6,
        "max_best_vs_2nd": 1.05,
        "min_best_vs_median": 1.03,
    },
    # mercados típicamente más manipulables / dispersos
    "high": {
        "min_books": 8,
        "max_best_vs_2nd": 1.03,
        "min_best_vs_median": 1.05,
    },
    # mercados altamente volátiles (correct score / scorers / exactas)
    "extreme": {
        "min_books": 10,
        "max_best_vs_2nd": 1.02,
        "min_best_vs_median": 1.06,
    },
}


def _norm_str(x: Any) -> str:
    return str(x).strip() if x is not None else ""


def _p_implied(odds: float) -> float:
    return 1.0 / odds if odds and odds > 0 else 0.0


def _get_p_est(item: Dict[str, Any]) -> Optional[float]:
    # En odds_premium pueden existir distintos nombres; fallback seguro.
    for k in ("p_estimated", "pEstimated", "p_est", "pEst", "probability", "p"):
        v = item.get(k)
        if v is None:
            continue
        try:
            return float(v)
        except Exception:
            continue
    return None


def _classify_market(market: str) -> Dict[str, str]:
    """
    Clasificación heurística, auditable y extensible.
    No filtra: SIEMPRE devuelve algo para cualquier market.
    """
    m = _norm_str(market).lower()

    # Correct score / exactas / scorers -> extrema
    if "correct score" in m or "exact" in m or "first goal scorer" in m or "last goal scorer" in m or "anytime goal scorer" in m:
        return {"marketType": "exotics", "marketRisk": "extreme"}

    # Totales (Over/Under, Team Total, Totals por periodos) -> low/medium
    if "over/under" in m or "total" in m:
        # totales por periodo tienden a más varianza que full game, pero siguen siendo relativamente líquidos
        if "1st" in m or "2nd" in m or "3rd" in m or "quarter" in m or "period" in m or "half" in m:
            return {"marketType": "totals", "marketRisk": "medium"}
        return {"marketType": "totals", "marketRisk": "low"}

    # Handicap / Asian handicap -> medium
    if "handicap" in m:
        # segmentos tipo 1st half / qtr -> un poco más volátil
        if "1st" in m or "2nd" in m or "quarter" in m or "period" in m or "half" in m:
            return {"marketType": "handicap", "marketRisk": "medium"}
        return {"marketType": "handicap", "marketRisk": "medium"}

    # Mercados de resultado (3way, double chance, ht/ft, home/away) -> medium
    if "3way" in m or "double chance" in m or "ht/ft" in m or "home/away" in m or m == "home/away":
        return {"marketType": "result", "marketRisk": "medium"}

    if "odd/even" in m:
        return {"marketType": "props", "marketRisk": "high"}

    # Default conservador
    return {"marketType": "other", "marketRisk": "high"}


def build_pools(day: str) -> Dict[str, Any]:
    src = f"api/data/odds_premium/{day}/all.json"
    if not os.path.exists(src):
        raise FileNotFoundError(src)

    with open(src, "r") as f:
        rows = json.load(f)

    grouped: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        sport = _norm_str(r.get("sport"))
        event_id = _norm_str(r.get("eventId"))
        market = _norm_str(r.get("market"))
        selection = _norm_str(r.get("selection"))
        if not (sport and event_id and market and selection):
            continue
        grouped[(sport, event_id, market, selection)].append(r)

    inflated: List[Dict[str, Any]] = []
    parlay_eligible: List[Dict[str, Any]] = []

    for (sport, event_id, market, selection), items in grouped.items():
        # odds list
        odds_list: List[float] = []
        for i in items:
            try:
                odds_list.append(float(i.get("odds")))
            except Exception:
                pass
        odds_list.sort(reverse=True)
        if len(odds_list) < 2:
            continue

        # best/2nd/median
        best = odds_list[0]
        second = odds_list[1]
        median = statistics.median(odds_list)

        # best item (para p_est asociado)
        best_item = None
        best_odds_seen = -1.0
        for it in items:
            try:
                o = float(it.get("odds"))
            except Exception:
                continue
            if o > best_odds_seen:
                best_odds_seen = o
                best_item = it
        if not best_item:
            continue

        p_est = _get_p_est(best_item)
        if p_est is None:
            continue

        # Clasificación del market (para TODOS)
        meta = _classify_market(market)
        mrisk = meta["marketRisk"]
        thr = THRESHOLDS.get(mrisk, THRESHOLDS["high"])

        # Baseline para ser "parlay_eligible": datos suficientes + estabilidad mínima
        # (esto es fallback: más amplio que inflated)
        # Nota: NO exige edge > 0
        if len(odds_list) >= max(4, int(thr["min_books"]) - 2) and second > 0 and median > 0:
            parlay_eligible.append({
                "sport": sport,
                "eventId": event_id,
                "market": market,
                "selection": selection,
                "odds": round(best, 2),
                "probability": round(float(p_est), 4),
                "edge": round(float(p_est - _p_implied(best)), 4),
                "n_books": int(len(odds_list)),
                "best_vs_2nd": round(float(best / second), 4) if second > 0 else None,
                "best_vs_median": round(float(best / median), 4) if median > 0 else None,
                "consensus": "high" if len(odds_list) >= 10 else ("medium" if len(odds_list) >= 7 else "low"),
                "marketType": meta["marketType"],
                "marketRisk": meta["marketRisk"],
                "inflated": False,
            })

        # Regla de Inflada (más estricta) - contempla TODOS los markets
        if best < ODDS_MIN:
            continue
        if len(odds_list) < int(thr["min_books"]):
            continue
        if second <= 0 or median <= 0:
            continue

        best_vs_2nd = best / second
        best_vs_median = best / median

        if best_vs_2nd > float(thr["max_best_vs_2nd"]):
            continue
        if best_vs_median < float(thr["min_best_vs_median"]):
            continue

        edge = float(p_est) - _p_implied(best)
        if edge <= 0:
            continue

        consensus = "high" if len(odds_list) >= (int(thr["min_books"]) + 2) else "medium"

        inflated.append({
            "sport": sport,
            "eventId": event_id,
            "market": market,
            "selection": selection,
            "odds": round(best, 2),
            "probability": round(float(p_est), 4),
            "edge": round(float(edge), 4),

            "n_books": int(len(odds_list)),
            "best_vs_2nd": round(float(best_vs_2nd), 4),
            "best_vs_median": round(float(best_vs_median), 4),

            # 4 variables explícitas
            "consensus": consensus,
            "marketType": meta["marketType"],
            "marketRisk": meta["marketRisk"],
            "inflated": True,
        })

    out_dir = str(ensure_dir(data_path("pools", day)))
    os.makedirs(out_dir, exist_ok=True)

    with open(f"{out_dir}/inflated.json", "w") as f:
        json.dump(inflated, f, indent=2)

    with open(f"{out_dir}/parlay_eligible.json", "w") as f:
        json.dump(parlay_eligible, f, indent=2)

    return {
        "day": day,
        "groups_total": len(grouped),
        "inflated_count": len(inflated),
        "parlay_eligible_count": len(parlay_eligible),
        "sample_inflated": inflated[0] if inflated else None,
        "src": src,
        "out_dir": out_dir,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 api/services/inflated_pool_builder.py YYYY-MM-DD")
    summary = build_pools(sys.argv[1])
    print(json.dumps(summary, indent=2))
