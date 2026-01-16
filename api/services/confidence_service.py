from typing import Dict


def classify_streak(streak: int) -> str:
    if streak >= 5:
        return "HOT"
    if streak >= 3:
        return "GOOD"
    if streak >= 1:
        return "NORMAL"
    return "COLD"


def bot_confidence(roi: float, win_rate: float, streak: int) -> Dict:
    score = 0

    if roi >= 20:
        score += 2
    elif roi >= 5:
        score += 1

    if win_rate >= 65:
        score += 2
    elif win_rate >= 55:
        score += 1

    if streak >= 5:
        score += 2
    elif streak >= 3:
        score += 1

    if score >= 5:
        level = "VERY_HIGH"
        message = "Confianza muy alta 🔥"
    elif score >= 3:
        level = "HIGH"
        message = "Alta confianza ✅"
    elif score >= 1:
        level = "MEDIUM"
        message = "Confianza moderada ⚠️"
    else:
        level = "LOW"
        message = "Baja confianza ❌"

    return {
        "level": level,
        "message": message,
        "score": score
    }
