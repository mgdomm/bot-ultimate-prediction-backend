from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional


# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


MARKET_ADJUSTMENTS = {
    "Match Winner": 0.00,
    "Over/Under": 0.02,
    "Goals Over/Under": 0.02,
    "Goals Over/Under First Half": 0.01,
    "Goals Over/Under - Second Half": 0.01,
    "Both Teams Score": 0.01,
    "Home/Away": 0.00,
    "Second Half Winner": -0.05,
    "First Half Winner": -0.05,
    "Exact Score": -0.15,
}


def clamp(value: float, min_value: float = 0.01, max_value: float = 0.99) -> float:
    return max(min_value, min(max_value, value))


def estimate_probability(item: Dict[str, Any]) -> float:
    p_base = float(item["p_implied"])
    odds = float(item["odds"])
    market = item.get("market")

    market_adj = MARKET_ADJUSTMENTS.get(market, -0.03)

    if odds < 1.50:
        odds_adj = -0.05
    elif odds > 3.50:
        odds_adj = -0.07
    else:
        odds_adj = 0.00

    p_estimated = p_base + market_adj + odds_adj
    return round(clamp(p_estimated), 4)


def estimate_odds_for_day(day: Optional[str] = None) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    in_path = API_DATA_DIR / "odds_enriched" / day / "all.json"
    out_dir = API_DATA_DIR / "odds_estimated" / day
    out_file = out_dir / "all.json"

    if not in_path.exists():
        raise FileNotFoundError(f"No enriched odds file found: {in_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    odds_list = json.loads(in_path.read_text(encoding="utf-8"))

    estimated = []
    for item in odds_list:
        p_estimated = estimate_probability(item)

        estimated.append({
            "sport": item["sport"],
            "eventId": item["eventId"],
            "bookmaker": item.get("bookmaker"),
            "market": item.get("market"),
            "selection": item.get("selection"),
            "odds": float(item["odds"]),
            "p_implied": float(item["p_implied"]),
            "p_estimated": p_estimated,
        })

    out_file.write_text(json.dumps(estimated, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"day": day, "records": len(estimated), "output": str(out_file)}


if __name__ == "__main__":
    print(json.dumps(estimate_odds_for_day(), ensure_ascii=False, indent=2))
