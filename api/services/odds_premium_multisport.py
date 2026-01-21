from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

PREMIUM_PROBABILITY_THRESHOLD = 0.86
MIN_PREMIUM_PER_DAY = 2

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def _f(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


def _risk_level(sel: Dict[str, Any]) -> str:
    return (sel.get("risk") or {}).get("level") or "?"


def _key(sel: Dict[str, Any]) -> Tuple[str, str, str, str]:
    return (
        str(sel.get("sport") or ""),
        str(sel.get("eventId") or ""),
        str(sel.get("market") or ""),
        str(sel.get("selection") or ""),
    )


def is_premium_strict(sel: Dict[str, Any]) -> bool:
    # Definición estricta original (puede dar 0; transparencia total)
    return (_risk_level(sel) == "LOW") and (_f(sel.get("p_estimated")) >= PREMIUM_PROBABILITY_THRESHOLD)


def run_for_day(day: Optional[str] = None) -> Dict[str, Any]:
    if day is None:
        day = date.today().isoformat()

    in_path = API_DATA_DIR / "odds_risk" / day / "all.json"
    out_dir = API_DATA_DIR / "odds_premium" / day
    out_file = out_dir / "all.json"

    if not in_path.exists():
        raise FileNotFoundError(f"No risk file found: {in_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(in_path.read_text(encoding="utf-8"))

    # 1) Premium estricto
    strict_count = 0
    for sel in data:
        prem = is_premium_strict(sel)
        sel["premium"] = prem
        if prem:
            strict_count += 1
            sel["premium_reason"] = "STRICT_LOW_AND_HIGH_P"
        else:
            sel.pop("premium_reason", None)

    # 2) Fallback determinista: asegurar MIN_PREMIUM_PER_DAY si hay candidatos reales
    # Candidatos: EV>0 y risk in {LOW, MEDIUM}
    if strict_count < MIN_PREMIUM_PER_DAY:
        best_by_key: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}

        for sel in data:
            if sel.get("premium") is True:
                continue
            r = _risk_level(sel)
            if r not in {"LOW", "MEDIUM"}:
                continue
            if _f(sel.get("ev"), default=-1e9) <= 0:
                continue

            k = _key(sel)
            cur = best_by_key.get(k)
            if cur is None or _f(sel.get("ev")) > _f(cur.get("ev")):
                best_by_key[k] = sel

        cands = list(best_by_key.values())

        # Orden determinista (probabilidad primero, luego EV, luego odds más baja)
        cands.sort(
            key=lambda x: (
                -_f(x.get("p_estimated")),
                -_f(x.get("ev")),
                _f(x.get("odds"), default=999.0),
                _key(x),
            )
        )

        need = MIN_PREMIUM_PER_DAY - strict_count
        picked = 0
        for sel in cands:
            if picked >= need:
                break
            sel["premium"] = True
            sel["premium_reason"] = "FALLBACK_TOP2_MEDIUM_OR_LOW_EV_POS"
            picked += 1

    premium_total = sum(1 for sel in data if sel.get("premium") is True)

    out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "day": day,
        "records": len(data),
        "premium_total": premium_total,
        "premium_strict": strict_count,
        "output": str(out_file),
    }


if __name__ == "__main__":
    print(json.dumps(run_for_day(), ensure_ascii=False, indent=2))
