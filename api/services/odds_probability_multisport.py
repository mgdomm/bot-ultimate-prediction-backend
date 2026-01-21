from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional


# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def enrich_odds_with_implied_probability(day: Optional[str] = None) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    in_path = API_DATA_DIR / "odds_normalized" / day / "all.json"
    out_dir = API_DATA_DIR / "odds_enriched" / day
    out_file = out_dir / "all.json"

    if not in_path.exists():
        raise FileNotFoundError(f"No normalized odds file found: {in_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    odds_list = json.loads(in_path.read_text(encoding="utf-8"))

    enriched = []
    for item in odds_list:
        try:
            odds = float(item["odds"])
            p_implied = 1 / odds if odds > 0 else None
            if p_implied is None:
                continue
        except Exception:
            continue

        enriched.append({
            "sport": item["sport"],
            "eventId": item["eventId"],
            "bookmaker": item.get("bookmaker"),
            "market": item.get("market"),
            "selection": item.get("selection"),
            "odds": odds,
            "p_implied": round(p_implied, 4),
        })

    out_file.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"day": day, "records": len(enriched), "output": str(out_file)}


if __name__ == "__main__":
    print(json.dumps(enrich_odds_with_implied_probability(), ensure_ascii=False, indent=2))
