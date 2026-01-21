import os
import json
from datetime import datetime

SPORT_DEFAULT = "football"

def normalize_odds_for_today():
    today = datetime.now().strftime("%Y-%m-%d")

    raw_path = f"data/odds/{today}/football.json"
    out_dir = f"data/odds_normalized/{today}"
    out_file = f"{out_dir}/all.json"

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"No RAW odds file found: {raw_path}")

    os.makedirs(out_dir, exist_ok=True)

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_odds = json.load(f)

    normalized = []

    for fixture_block in raw_odds:
        fixture_id = fixture_block.get("fixture")
        payload = fixture_block.get("response")

        if not payload:
            continue

        for item in payload.get("response", []):
            bookmakers = item.get("bookmakers", [])

            for bookmaker in bookmakers:
                bookmaker_name = bookmaker.get("name")
                bets = bookmaker.get("bets", [])

                for bet in bets:
                    market = bet.get("name")
                    values = bet.get("values", [])

                    for value in values:
                        normalized.append({
                            "sport": SPORT_DEFAULT,
                            "eventId": fixture_id,
                            "bookmaker": bookmaker_name,
                            "market": market,
                            "selection": value.get("value"),
                            "odds": value.get("odd")
                        })

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)

    return {
        "date": today,
        "records": len(normalized),
        "output": out_file
}
