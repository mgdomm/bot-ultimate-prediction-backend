import os
import requests
from typing import Optional, Dict

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://v3.football.api-sports.io"


def get_football_result(bet: Dict) -> Optional[Dict]:
    """
    Devuelve el resultado oficial del evento si está finalizado.
    Si el partido no ha terminado, devuelve None.
    """

    if not API_KEY:
        raise RuntimeError("API_FOOTBALL_KEY not set")

    fixture_id = bet.get("eventId")
    if not fixture_id:
        return None

    headers = {
        "x-apisports-key": API_KEY
    }

    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={"id": fixture_id},
        timeout=10
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if not data.get("response"):
        return None

    fixture = data["response"][0]
    status = fixture["fixture"]["status"]["short"]

    # Partido no finalizado
    if status not in ("FT", "AET", "PEN"):
        return None

    goals = fixture["goals"]

    return {
        "home": goals["home"],
        "away": goals["away"],
        "status": status
    }
