"""
Mapa determinista sport -> base_url para API-SPORTS.
Validado por evidencia (DNS + /status + /leagues) en 2026-01-17.

Regla: UNA sola key (API_SPORTS_KEY) para todos los productos.
"""

SPORT_BASE_URL = {
    "football": "https://v3.football.api-sports.io",
    "afl": "https://v1.afl.api-sports.io",
    "baseball": "https://v1.baseball.api-sports.io",
    "basketball": "https://v1.basketball.api-sports.io",
    "formula-1": "https://v1.formula-1.api-sports.io",
    "handball": "https://v1.handball.api-sports.io",
    "hockey": "https://v1.hockey.api-sports.io",
    "mma": "https://v1.mma.api-sports.io",
    "rugby": "https://v1.rugby.api-sports.io",
    "volleyball": "https://v1.volleyball.api-sports.io",
    # APIs del panel:
    "nba": "https://v2.nba.api-sports.io",
    # NFL en el panel corresponde a American-Football:
    "nfl": "https://v1.american-football.api-sports.io",
}

# No disponible hoy (DNS fail + no aparece en panel):
DISABLED_SPORTS = {
    "tennis": "DNS_FAIL / no disponible en panel (2026-01-17)",
}
