from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

STAKE_DEFAULT = 50.0

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def classify_risk(selection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    odds = selection.get("odds")
    p_est = selection.get("p_estimated")
    p_impl = selection.get("p_implied")
    ev = selection.get("ev")

    if odds is None or p_est is None or p_impl is None or ev is None:
        return None

    odds = float(odds)
    p_est = float(p_est)
    p_impl = float(p_impl)
    ev = float(ev)

    delta_p = p_est - p_impl
    ev_margin = ev / STAKE_DEFAULT

    if (p_est < 0.50) or (ev_margin < 0.02) or (odds > 5.00):
        level = "EXTREME"
    elif (p_est >= 0.78) and (odds <= 1.65) and (ev_margin >= 0.02) and (abs(delta_p) <= 0.04):
        level = "LOW"
    elif (p_est >= 0.65) and (odds <= 2.20) and (ev_margin >= 0.025):
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "level": level,
        "p_est": round(p_est, 4),
        "delta_p": round(delta_p, 4),
        "ev_margin": round(ev_margin, 4),
    }


def run_for_day(day: Optional[str] = None) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    in_path = API_DATA_DIR / "odds_ev" / day / "all.json"
    out_dir = API_DATA_DIR / "odds_risk" / day
    out_file = out_dir / "all.json"

    if not in_path.exists():
        raise FileNotFoundError(f"No EV odds file found: {in_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(in_path.read_text(encoding="utf-8"))

    kept = 0
    for sel in data:
        risk = classify_risk(sel)
        if risk:
            sel["risk"] = risk
            kept += 1

    out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"day": day, "records": len(data), "with_risk": kept, "output": str(out_file)}


if __name__ == "__main__":
    print(json.dumps(run_for_day(), ensure_ascii=False, indent=2))
