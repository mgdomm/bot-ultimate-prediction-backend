from datetime import date
import os
import json

from services.bet_generator import generate_daily_bets
from services.premium_service import apply_premium_flags
from services.contract_service import normalize_and_validate_bets
from services.confidence_service import bot_confidence
from services.stats_service import (
    calculate_roi,
    win_rate,
    current_streak,
    distribution_by_sport
)

DATA_DIR = "data/contracts"


def build_daily_contract() -> dict:
    today = date.today().isoformat()
    day_dir = os.path.join(DATA_DIR, today)
    os.makedirs(day_dir, exist_ok=True)

    contract_path = os.path.join(day_dir, "contract.json")

    # ✅ Idempotencia
    if os.path.exists(contract_path):
        with open(contract_path, "r") as f:
            return json.load(f)

    # 1️⃣ Generar bets
    daily = generate_daily_bets()
    classic = daily.get("classic", [])
    parlay = daily.get("parlay", [])

    # 2️⃣ Premium
    classic = apply_premium_flags(classic)["bets"]
    parlay = apply_premium_flags(parlay)["bets"]

    # 3️⃣ Normalizar + validar (estricto)
    classic, classic_errors = normalize_and_validate_bets(
        classic, bet_type="classic", strict=True, default_stake=50.0
    )
    parlay, parlay_errors = normalize_and_validate_bets(
        parlay, bet_type="parlay", strict=True, default_stake=50.0
    )

    if classic_errors or parlay_errors:
        raise RuntimeError({
            "classicErrors": classic_errors,
            "parlayErrors": parlay_errors,
        })

    # 4️⃣ Stats + confianza (placeholder realista)
    history = []
    stats = {
        "roi": calculate_roi(history),
        "winRate": win_rate(history),
        "currentStreak": current_streak(history),
        "distributionBySport": distribution_by_sport(history),
    }

    confidence = bot_confidence(
        roi=stats["roi"],
        win_rate=stats["winRate"],
        streak=stats["currentStreak"]
    )

    payload = {
        "_meta": {
            "date": today,
            "locked": True,
            "source": "contract_builder",
        },
        "classic": classic,
        "parlay": parlay,
        "confidence": confidence,
    }

    with open(contract_path, "w") as f:
        json.dump(payload, f, indent=2)

    return payload
