from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_STAKE = 50.0

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def calculate_ev(p_estimated: float, odds: float, stake: float) -> float:
    return (p_estimated * odds - 1.0) * stake


def calculate_ev_for_day(day: Optional[str] = None, stake: float = DEFAULT_STAKE) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    in_path = API_DATA_DIR / "odds_estimated" / day / "all.json"
    out_dir = API_DATA_DIR / "odds_ev" / day
    out_file = out_dir / "all.json"

    if not in_path.exists():
        raise FileNotFoundError(f"No estimated odds file found: {in_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    odds_list = json.loads(in_path.read_text(encoding="utf-8"))

    enriched = []
    for item in odds_list:
        ev = calculate_ev(
            p_estimated=float(item["p_estimated"]),
            odds=float(item["odds"]),
            stake=float(stake),
        )

        enriched.append({
            "sport": item["sport"],
            "eventId": item["eventId"],
            "bookmaker": item.get("bookmaker"),
            "market": item.get("market"),
            "selection": item.get("selection"),
            "odds": float(item["odds"]),
            "p_implied": float(item["p_implied"]),
            "p_estimated": float(item["p_estimated"]),
            "stake": float(stake),
            "ev": round(ev, 2),
        })

    out_file.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"day": day, "records": len(enriched), "stake": stake, "output": str(out_file)}


if __name__ == "__main__":
    print(json.dumps(calculate_ev_for_day(), ensure_ascii=False, indent=2))
