from fastapi import FastAPI, HTTPException
from datetime import date, datetime
import json
import os

from services.bet_generator import generate_daily_bets
from services.premium_service import apply_premium_flags
from services.confidence_service import bot_confidence
from services.contract_service import normalize_and_validate_bets
from services.stats_service import (
    calculate_roi,
    win_rate,
    current_streak,
    best_and_worst_days,
    distribution_by_sport
)
from services.settlement_service import settle_all_pending_bets

app = FastAPI(title="Bot Ultimate Prediction API")

DATA_DIR = "data"
HISTORY_FILE = "history.json"


# ✅ Liquidación automática al arranque (backend, no script)
try:
    settle_all_pending_bets()
except Exception as e:
    print(f"[WARN] Settlement skipped: {e}")


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)


def get_stats():
    bets = load_history()

    best_day, worst_day = best_and_worst_days(bets)

    return {
        "roi": calculate_roi(bets),
        "winRate": win_rate(bets),
        "currentStreak": current_streak(bets),
        "bestDay": best_day,
        "worstDay": worst_day,
        "distributionBySport": distribution_by_sport(bets)
    }


def is_locked(payload: dict) -> bool:
    return payload.get("_meta", {}).get("locked", False)


def select_top3_premium(bets):
    """
    Devuelve hasta 3 bets Premium como SUBCONJUNTO de 'bets', sin IDs duplicados.
    Orden estable: premiumScore desc, totalProbability desc, totalOdds desc.
    """
    if bets is None or not isinstance(bets, list):
        return []

    premium = [b for b in bets if isinstance(b, dict) and b.get("isPremium")]

    def key(b):
        ps = b.get("premiumScore") or 0.0
        tp = b.get("totalProbability") or 0.0
        to = b.get("totalOdds") or 0.0
        try:
            ps = float(ps)
        except Exception:
            ps = 0.0
        try:
            tp = float(tp)
        except Exception:
            tp = 0.0
        try:
            to = float(to)
        except Exception:
            to = 0.0
        return (-ps, -tp, -to)

    premium_sorted = sorted(premium, key=key)

    out = []
    seen = set()
    for b in premium_sorted:
        bid = b.get("id")
        if not bid or bid in seen:
            continue
        seen.add(bid)
        out.append(b)
        if len(out) == 3:
            break
    return out


@app.get("/bets/today")
def get_today_bets():
    today = date.today().isoformat()
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, f"{today}.json")

    # ✅ Si existe y está sellado → VALIDAR contrato antes de devolver (POLICY=reject)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            payload = json.load(f)
            if is_locked(payload):
                classic = payload.get("classic", None)
                parlay = payload.get("parlay", None)
                top3c = payload.get("premiumTop3Classic", None)
                top3p = payload.get("premiumTop3Parlay", None)

                _, classic_errors = normalize_and_validate_bets(
                    classic, bet_type="classic", strict=True, default_stake=50.0
                )
                _, parlay_errors = normalize_and_validate_bets(
                    parlay, bet_type="parlay", strict=True, default_stake=50.0
                )
                _, top3c_errors = normalize_and_validate_bets(
                    top3c, bet_type="classic", strict=True, default_stake=50.0
                )
                _, top3p_errors = normalize_and_validate_bets(
                    top3p, bet_type="parlay", strict=True, default_stake=50.0
                )

                if classic_errors or parlay_errors or top3c_errors or top3p_errors:
                    raise HTTPException(
                        status_code=500,
                        detail={
                            "message": "Locked day violates contract. Refusing to serve locked payload (POLICY=reject).",
                            "file": str(file_path),
                            "classicErrors": classic_errors,
                            "parlayErrors": parlay_errors,
                            "premiumTop3ClassicErrors": top3c_errors,
                            "premiumTop3ParlayErrors": top3p_errors,
                        },
                    )

                return payload

    # ✅ 1. Generar apuestas (generate_daily_bets retorna dict: {"classic": [], "parlay": []})
    daily = generate_daily_bets()
    classic_bets = daily.get("classic", [])
    parlay_bets = daily.get("parlay", [])

    # ✅ 2. Premium separado
    classic_result = apply_premium_flags(classic_bets)
    parlay_result = apply_premium_flags(parlay_bets)

    classic_bets = classic_result["bets"]
    parlay_bets = parlay_result["bets"]

    # ✅ 3. Normalizar y validar CONTRATO (estricto) antes de sellar el día
    classic_norm, classic_errors = normalize_and_validate_bets(
        classic_bets, bet_type="classic", strict=True, default_stake=50.0
    )
    parlay_norm, parlay_errors = normalize_and_validate_bets(
        parlay_bets, bet_type="parlay", strict=True, default_stake=50.0
    )

    if classic_errors or parlay_errors:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Contract validation failed. Day NOT locked. Fix generator/backend to satisfy contract.",
                "classicErrors": classic_errors,
                "parlayErrors": parlay_errors,
            },
        )

    classic_bets = classic_norm
    parlay_bets = parlay_norm

    premium_classic = select_top3_premium(classic_bets)
    premium_parlay = select_top3_premium(parlay_bets)

    total_premium = (
        len([b for b in classic_bets if b.get("isPremium")]) +
        len([b for b in parlay_bets if b.get("isPremium")])
    )

    stats = get_stats()
    confidence = bot_confidence(
        roi=stats["roi"],
        win_rate=stats["winRate"],
        streak=stats["currentStreak"]
    )

    payload = {
        "premiumMessage": (
            f"{total_premium} selecciones Premium hoy. "
            f"{confidence['message']} "
            "Apuestas con valor esperado positivo, no seguras."
        ),
        "premiumTop3Classic": premium_classic,
        "premiumTop3Parlay": premium_parlay,
        "classic": classic_bets,
        "parlay": parlay_bets,
        "_meta": {
            "date": today,
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "locked": True,
            "version": "1.0"
        }
    }

    with open(file_path, "w") as f:
        json.dump(payload, f, indent=2)

    return payload


@app.get("/stats")
def stats():
    return get_stats()
