from typing import List, Dict, Optional
from functools import reduce

TARGET_NET_PROFIT_FEATURED = 500.00

FALLBACK_LEVELS = [
    {"min_prob": 0.72, "min_legs": 2, "max_legs": 4, "risk": "HIGH"},
    {"min_prob": 0.68, "min_legs": 2, "max_legs": 4, "risk": "HIGH"},
    {"min_prob": 0.65, "min_legs": 2, "max_legs": 2, "risk": "VERY_HIGH"},
]


def _product(values: List[float]) -> float:
    return reduce(lambda x, y: x * y, values)


def build_featured_parlay(picks: List[Dict]) -> Optional[Dict]:
    """
    Construye un DAILY_FEATURED_PARLAY usando fallback controlado.
    No persiste nada. Solo devuelve el dict o None.
    """
    for level in FALLBACK_LEVELS:
        eligible = [
            p for p in picks
            if p.get("prob_estimada") is not None
            and p["prob_estimada"] >= level["min_prob"]
        ]

        if len(eligible) < level["min_legs"]:
            continue

        eligible.sort(key=lambda x: x["prob_estimada"], reverse=True)
        legs = eligible[: level["max_legs"]]

        combined_odds = _product([l["odds"] for l in legs])
        prob_parlay = _product([l["prob_estimada"] for l in legs])

        stake = TARGET_NET_PROFIT_FEATURED / (combined_odds - 1)
        stake = round(stake, 2)

        return {
            "type": "DAILY_FEATURED_PARLAY",
            "risk_level": level["risk"],
            "fallback_min_prob": level["min_prob"],
            "legs": legs,
            "combined_odds": round(combined_odds, 2),
            "prob_parlay": round(prob_parlay, 4),
            "stake_eur": stake,
            "max_loss_eur": stake,
            "target_profit_eur": TARGET_NET_PROFIT_FEATURED,
            "potential_return_eur": round(stake * combined_odds, 2),
        }

    return None

from datetime import date
from pathlib import Path
import json


def save_featured_parlay(parlay: Dict) -> None:
    today = date.today().isoformat()
    base_path = Path(f"api/data/picks_parlay_featured/{today}")
    base_path.mkdir(parents=True, exist_ok=True)

    file_path = base_path / "featured_parlay.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(parlay, f, ensure_ascii=False, indent=2)
