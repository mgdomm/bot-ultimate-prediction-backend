import os
import json
from datetime import datetime

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

def clamp(value, min_value=0.01, max_value=0.99):
    return max(min_value, min(max_value, value))

def estimate_probability(item):
    p_base = item["p_implied"]
    odds = item["odds"]
    market = item["market"]

    # Market adjustment
    market_adj = MARKET_ADJUSTMENTS.get(market, -0.03)

    # Odds adjustment
    if odds < 1.50:
        odds_adj = -0.05
    elif odds > 3.50:
        odds_adj = -0.07
    else:
        odds_adj = 0.00

    p_estimated = p_base + market_adj + odds_adj
    return round(clamp(p_estimated), 4)

def estimate_odds_for_today():
    today = datetime.now().strftime("%Y-%m-%d")

    in_path = f"data/odds_enriched/{today}/all.json"
    out_dir = f"data/odds_estimated/{today}"
    out_file = f"{out_dir}/all.json"

    if not os.path.exists(in_path):
        raise FileNotFoundError(f"No enriched odds file found: {in_path}")

    os.makedirs(out_dir, exist_ok=True)

    with open(in_path, "r", encoding="utf-8") as f:
        odds_list = json.load(f)

    estimated = []

    for item in odds_list:
        p_estimated = estimate_probability(item)

        estimated.append({
            "sport": item["sport"],
            "eventId": item["eventId"],
            "bookmaker": item["bookmaker"],
            "market": item["market"],
            "selection": item["selection"],
            "odds": item["odds"],
            "p_implied": item["p_implied"],
            "p_estimated": p_estimated
        })

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(estimated, f, indent=2, ensure_ascii=False)

    return {
        "date": today,
        "records": len(estimated),
        "output": out_file
}
