from typing import Dict


def evaluate_bet(bet: Dict, result: Dict) -> str:
    """
    Devuelve: 'win', 'lose' o 'void'
    """

    market = bet.get("market", "").lower()
    selections = bet.get("selections", [])

    if not market or not selections:
        return "void"

    home_goals = result["home"]
    away_goals = result["away"]
    total_goals = home_goals + away_goals

    selection = selections[0].lower()

    # 1️⃣ 1X2
    if market == "1x2":
        if selection == "home" and home_goals > away_goals:
            return "win"
        if selection == "draw" and home_goals == away_goals:
            return "win"
        if selection == "away" and away_goals > home_goals:
            return "win"
        return "lose"

    # 2️⃣ Doble oportunidad
    if market == "double_chance":
        if selection == "1x" and home_goals >= away_goals:
            return "win"
        if selection == "12" and home_goals != away_goals:
            return "win"
        if selection == "x2" and away_goals >= home_goals:
            return "win"
        return "lose"

    # 3️⃣ Over / Under
    if market.startswith("over"):
        line = float(market.replace("over", ""))
        return "win" if total_goals > line else "lose"

    if market.startswith("under"):
        line = float(market.replace("under", ""))
        return "win" if total_goals < line else "lose"

    # 4️⃣ BTTS
    if market == "btts":
        if selection == "yes" and home_goals > 0 and away_goals > 0:
            return "win"
        if selection == "no" and (home_goals == 0 or away_goals == 0):
            return "win"
        return "lose"

    return "void"
