# services/sports_config.py
# Configuración unificada y auditable de deportes y mercados

import random

# Deportes habilitados en el sistema
ENABLED_SPORTS = {
    "football": {
        "label": "Football",
        "markets": [
            "match_winner",
            "over_2_5",
            "under_2_5",
            "both_teams_score",
            "double_chance"
        ]
    },
    "basketball": {
        "label": "Basketball",
        "markets": [
            "match_winner",
            "over_points",
            "under_points"
        ]
    },
    "tennis": {
        "label": "Tennis",
        "markets": [
            "match_winner",
            "set_winner"
        ]
    }
}

def get_enabled_sports():
    """
    Devuelve la lista de deportes habilitados.
    """
    return list(ENABLED_SPORTS.keys())

def get_markets_for_sport(sport: str):
    """
    Devuelve los mercados válidos para un deporte.
    """
    config = ENABLED_SPORTS.get(sport)
    if not config:
        return []
    return config.get("markets", [])

def get_random_market(sport: str):
    """
    Selecciona un mercado aleatorio válido para un deporte.
    """
    markets = get_markets_for_sport(sport)
    if not markets:
        return None
    return random.choice(markets)
