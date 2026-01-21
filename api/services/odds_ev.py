import os
import json
from datetime import datetime

DEFAULT_STAKE = 50

def calculate_ev(p_estimated, odds, stake):
    return (p_estimated * odds - 1) * stake

def calculate_ev_for_today():
    today = datetime.now().strftime("%Y-%m-%d")

    in_path = f"data/odds_estimated/{today}/all.json"
    out_dir = f"data/odds_ev/{today}"
    out_file = f"{out_dir}/all.json"

    if not os.path.exists(in_path):
        raise FileNotFoundError(f"No estimated odds file found: {in_path}")

    os.makedirs(out_dir, exist_ok=True)

    with open(in_path, "r", encoding="utf-8") as f:
        odds_list = json.load(f)

    enriched = []

    for item in odds_list:
        ev = calculate_ev(
            p_estimated=item["p_estimated"],
            odds=item["odds"],
            stake=DEFAULT_STAKE
        )

        enriched.append({
            "sport": item["sport"],
            "eventId": item["eventId"],
            "bookmaker": item["bookmaker"],
            "market": item["market"],
            "selection": item["selection"],
            "odds": item["odds"],
            "p_implied": item["p_implied"],
            "p_estimated": item["p_estimated"],
            "stake": DEFAULT_STAKE,
            "ev": round(ev, 2)
        })

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    return {
        "date": today,
        "records": len(enriched),
        "stake": DEFAULT_STAKE,
        "output": out_file
}
