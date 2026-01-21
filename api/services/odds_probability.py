import os
import json
from datetime import datetime

def enrich_odds_with_implied_probability():
    today = datetime.now().strftime("%Y-%m-%d")

    in_path = f"data/odds_normalized/{today}/all.json"
    out_dir = f"data/odds_enriched/{today}"
    out_file = f"{out_dir}/all.json"

    if not os.path.exists(in_path):
        raise FileNotFoundError(f"No normalized odds file found: {in_path}")

    os.makedirs(out_dir, exist_ok=True)

    with open(in_path, "r", encoding="utf-8") as f:
        odds_list = json.load(f)

    enriched = []

    for item in odds_list:
        try:
            odds = float(item["odds"])
            p_implied = 1 / odds if odds > 0 else None
        except Exception:
            continue

        enriched.append({
            "sport": item["sport"],
            "eventId": item["eventId"],
            "bookmaker": item["bookmaker"],
            "market": item["market"],
            "selection": item["selection"],
            "odds": odds,
            "p_implied": round(p_implied, 4)
        })

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    return {
        "date": today,
        "records": len(enriched),
        "output": out_file
}
