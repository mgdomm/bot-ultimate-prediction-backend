# services/sports_config.py
# Configuración unificada y auditable de deportes y mercados

import random

ENABLED_SPORTS = {
    "football": {
        "code": "football",
        "name": "Football",
        "markets": [
            "match_winner",
            "over_2_5",
            "under_2_5",
            "both_teams_score",
            "double_chance"
        ]
    },
    "basketball": {
        "code": "basketball",
        "name": "Basketball",
        "markets": [
            "match_winner",
            "over_points",
            "under_points"
        ]
    },
    "tennis": {
        "code": "tennis",
        "name": "Tennis",
        "markets": [
            "match_winner",
            "set_winner"
        ]
    }
}

def get_enabled_sports():
    """
    Devuelve la lista de deportes habilitados como dicts {code, name, markets}.
    """
    return list(ENABLED_SPORTS.values())

def get_markets_for_sport(sport_code: str):
    sport = ENABLED_SPORTS.get(sport_code)
    if not sport:
        return []
    return sport.get("markets", [])

def get_random_market(sport_code: str):
    markets = get_markets_for_sport(sport_code)
    if not markets:
        return None
    return random.choice(markets)
