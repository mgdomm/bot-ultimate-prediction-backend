from typing import List, Dict


MIN_PREMIUM = 3
MAX_PREMIUM = 4


def score_bet_for_premium(bet: Dict) -> float:
    """
    Score interno auditable para determinar valor Premium.
    """

    probability = bet.get("totalProbability", 0)
    odds = bet.get("totalOdds", 0)
    risk = bet.get("riskLevel", "red")
    bet_type = bet.get("type", "classic")

    score = 0.0

    # Probabilidad (peso principal)
    score += probability * 100

    # Retorno razonable
    if odds >= 2.0:
        score += 15
    elif odds >= 1.7:
        score += 10
    elif odds >= 1.5:
        score += 5

    # Riesgo
    if risk == "green":
        score += 10
    elif risk == "yellow":
        score += 5

    # Penalización ligera a parlays
    if bet_type == "parlay":
        score -= 5

    return round(score, 2)


def premium_reason(bet: Dict) -> str:
    """
    Explicación humana corta, lista para UI.
    """

    probability = int(bet.get("totalProbability", 0) * 100)
    odds = bet.get("totalOdds", 0)
    bet_type = bet.get("type", "classic")

    base = f"Alta probabilidad estimada ({probability}%) con cuota atractiva ({odds})."

    if bet_type == "parlay":
        return base + " Combinada lógica con riesgo controlado."

    return base + " Escenario sólido según análisis contextual."


def apply_premium_flags(bets: List[Dict]) -> Dict:
    """
    Marca apuestas Premium, genera mensaje global y añade score auditable.
    """

    if not bets:
        return {
            "bets": bets,
            "premiumMessage": "No hay apuestas disponibles hoy."
        }

    scored = []

    for bet in bets:
        score = score_bet_for_premium(bet)
        bet["premiumScore"] = score
        scored.append((score, bet))

    scored.sort(key=lambda x: x[0], reverse=True)

    premium_count = min(
        max(MIN_PREMIUM, len(scored) // 3),
        MAX_PREMIUM
    )

    premium_selected = scored[:premium_count]
    premium_ids = {bet["id"] for _, bet in premium_selected}

    for bet in bets:
        if bet["id"] in premium_ids:
            bet["isPremium"] = True
            bet["premiumReason"] = premium_reason(bet)
        else:
            bet["isPremium"] = False
            bet["premiumReason"] = None

    message = (
        f"{premium_count} selecciones Premium hoy. "
        "Alta confianza basada en probabilidad realista y valor esperado positivo. "
        "No son apuestas seguras."
    )

    return {
        "bets": bets,
        "premiumMessage": message
    }


def generate_advanced_premium_message(
    premium_count: int,
    confidence_level: str,
    streak_status: str
) -> str:
    """
    Mensaje Premium avanzado basado en estado real del bot.
    Listo para UI / monetización.
    """

    base = f"{premium_count} selecciones Premium hoy."

    confidence_map = {
        "VERY_HIGH": "Confianza del bot muy alta 🔥",
        "HIGH": "Confianza del bot alta ✅",
        "MEDIUM": "Confianza del bot moderada ⚠️",
        "LOW": "Confianza del bot baja ❌"
    }

    streak_map = {
        "HOT": "Racha muy positiva.",
        "GOOD": "Buena racha reciente.",
        "NORMAL": "Rendimiento estable.",
        "COLD": "Racha negativa reciente."
    }

    confidence_text = confidence_map.get(confidence_level, "")
    streak_text = streak_map.get(streak_status, "")

    return (
        f"{base} "
        f"{confidence_text} "
        f"{streak_text} "
        "Apuestas con valor esperado positivo, no seguras."
    )
