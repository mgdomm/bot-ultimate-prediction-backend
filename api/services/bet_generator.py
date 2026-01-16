from typing import List, Dict
from datetime import datetime, timedelta
import random

from services.sports_config import get_enabled_sports, get_random_market


DEFAULT_STAKE = 50.0


def _round2(x: float) -> float:
    try:
        return float(f"{float(x):.2f}")
    except Exception:
        return 0.0


def _risk_from_p(p: float) -> str:
    # Heurística simple/auditable
    if p >= 0.65:
        return "green"
    if p >= 0.55:
        return "yellow"
    return "red"


def _classic_totals(selection: Dict) -> Dict:
    p = float(selection.get("probability") or 0.0)
    o = float(selection.get("odds") or 0.0)
    p = max(0.0, min(1.0, p))
    o = max(0.0, o)
    total_prob = _round2(p)
    total_odds = _round2(o)
    stake = _round2(DEFAULT_STAKE)
    potential_win = _round2(stake * total_odds)
    return {
        "totalProbability": total_prob,
        "totalOdds": total_odds,
        "stake": stake,
        "potentialWin": potential_win,
        "riskLevel": _risk_from_p(total_prob),
        "result": None,
    }


def _parlay_totals(selections: List[Dict]) -> Dict:
    prob = 1.0
    odds = 1.0
    for s in selections:
        p = float(s.get("probability") or 0.0)
        o = float(s.get("odds") or 0.0)
        p = max(0.0, min(1.0, p))
        o = max(0.0, o)
        prob *= p
        odds *= o

    total_prob = _round2(max(0.0, min(1.0, prob)))
    total_odds = _round2(max(0.0, odds))
    stake = _round2(DEFAULT_STAKE)
    potential_win = _round2(stake * total_odds)
    return {
        "totalProbability": total_prob,
        "totalOdds": total_odds,
        "stake": stake,
        "potentialWin": potential_win,
        "riskLevel": _risk_from_p(total_prob),
        "result": None,
    }


# =========================
# GENERADOR DE APUESTAS
# =========================

def generate_classic_bets(count: int = 10) -> List[Dict]:
    """
    Genera N apuestas clásicas distribuidas entre deportes habilitados.
    Incluye campos del contrato: totalProbability, totalOdds, stake, potentialWin, riskLevel, result.
    """
    sports = get_enabled_sports()
    now = datetime.utcnow()
    bets: List[Dict] = []

    for i in range(1, count + 1):
        sport = random.choice(sports)
        sport_code = sport["code"]
        sport_name = sport["name"]
        market = get_random_market(sport_code)

        # Probabilidad realista según deporte
        base_prob = random.uniform(0.68, 0.88)
        odds = _round2(1 / base_prob + random.uniform(0.05, 0.15))

        selection = {
            "name": f"Selección {sport_name}",
            "odds": odds,
            "probability": round(base_prob, 4)
        }

        bet = {
            "id": f"C{i}",
            "type": "classic",
            "title": f"{sport_name} - Partido #{i}",
            "sport": sport_code,
            "event": f"Evento {sport_name} #{i}",
            "market": market,
            "startTime": (now + timedelta(hours=random.randint(1, 12))).isoformat(),
            "status": "scheduled",
            "selections": [selection],
        }

        bet.update(_classic_totals(selection))
        bets.append(bet)

    return bets


def generate_parlay_bets(count: int = 10) -> List[Dict]:
    """
    Genera N parlays multideporte con variedad de estilos.
    Incluye campos del contrato: totalProbability, totalOdds, stake, potentialWin, riskLevel, result.
    """
    sports = get_enabled_sports()
    now = datetime.utcnow()
    parlays: List[Dict] = []

    # Configuración de estilos de parlay (se usan los 10 para producir exactamente 10)
    parlay_configs = [
        {"selections": 2, "style": "seguro", "prob_range": (0.78, 0.88)},
        {"selections": 2, "style": "futbol_mix", "prob_range": (0.72, 0.82)},
        {"selections": 2, "style": "alto_valor", "prob_range": (0.65, 0.75)},
        {"selections": 3, "style": "multideporte", "prob_range": (0.72, 0.82)},
        {"selections": 3, "style": "equilibrado", "prob_range": (0.70, 0.80)},
        {"selections": 3, "style": "cuota_alta", "prob_range": (0.62, 0.72)},
        {"selections": 3, "style": "seguro_multi", "prob_range": (0.75, 0.85)},
        {"selections": 4, "style": "jackpot_bajo", "prob_range": (0.72, 0.80)},
        {"selections": 4, "style": "jackpot_medio", "prob_range": (0.68, 0.76)},
        {"selections": 4, "style": "jackpot_alto", "prob_range": (0.60, 0.70)},
    ]

    style_names = {
        "seguro": "Parlay Seguro",
        "futbol_mix": "Parlay Fútbol Mix",
        "alto_valor": "Parlay Alto Valor",
        "multideporte": "Parlay Multideporte",
        "equilibrado": "Parlay Equilibrado",
        "cuota_alta": "Parlay Cuota Alta",
        "seguro_multi": "Parlay Seguro Multi",
        "jackpot_bajo": "Jackpot Conservador",
        "jackpot_medio": "Jackpot Moderado",
        "jackpot_alto": "Jackpot Agresivo",
    }

    for i, config in enumerate(parlay_configs[:count], 1):
        num_selections = config["selections"]
        style = config["style"]
        prob_min, prob_max = config["prob_range"]

        # Asegurar fútbol en estilos mixtos
        if style == "futbol_mix":
            football = next((s for s in sports if s["code"] == "football"), None)
            other_sports = [s for s in sports if s["code"] != "football"]
            if football and len(other_sports) >= (num_selections - 1):
                selected_sports = [football] + random.sample(other_sports, num_selections - 1)
            else:
                selected_sports = random.sample(sports, min(num_selections, len(sports)))
        else:
            selected_sports = random.sample(sports, min(num_selections, len(sports)))

        selections: List[Dict] = []
        for j, sport in enumerate(selected_sports):
            sport_code = sport["code"]
            sport_name = sport["name"]
            market = get_random_market(sport_code)

            base_prob = random.uniform(prob_min, prob_max)
            odds = _round2(1 / base_prob + random.uniform(0.05, 0.12))

            selections.append({
                "name": f"{sport_name} - Selección {j+1}",
                "sport": sport_code,
                "market": market,
                "odds": odds,
                "probability": round(base_prob, 4)
            })

        parlay = {
            "id": f"P{i}",
            "type": "parlay",
            "title": style_names.get(style, f"Parlay #{i}"),
            "sport": "multi",
            "event": f"Combinada {len(selections)} selecciones",
            "market": "Parlay",
            "startTime": (now + timedelta(hours=random.randint(2, 10))).isoformat(),
            "status": "scheduled",
            "selections": selections,
        }

        parlay.update(_parlay_totals(selections))
        parlays.append(parlay)

    return parlays


def generate_daily_bets() -> Dict[str, List[Dict]]:
    """
    Genera las 20 apuestas diarias:
    - 10 clásicas
    - 10 parlays
    """
    classic = generate_classic_bets(10)
    parlay = generate_parlay_bets(10)

    return {
        "classic": classic,
        "parlay": parlay
    }
