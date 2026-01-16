import os
import requests
from typing import Optional, Dict

API_KEY = os.getenv("THESPORTSDB_API_KEY", "1")
BASE_URL = "https://www.thesportsdb.com/api/v1/json"


def get_other_sport_result(bet: Dict) -> Optional[Dict]:
    """
    Devuelve el resultado oficial del evento si está finalizado.
    Si el evento no ha terminado, devuelve None.
    """

    event_id = bet.get("eventId")
    if not event_id:
        return None

    response = requests.get(
        f"{BASE_URL}/{API_KEY}/lookupevent.php",
        params={"id": event_id},
        timeout=10
    )

    if response.status_code != 200:
        return None

    data = response.json()
    events = data.get("events")

    if not events:
        return None

    event = events[0]

    # Si no hay marcador final, no está terminado
    if event.get("intHomeScore") is None or event.get("intAwayScore") is None:
        return None

    return {
        "home": int(event["intHomeScore"]),
        "away": int(event["intAwayScore"]),
        "status": "FT"
    }
