import json
from typing import List, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

from api.utils.paths import data_path
from api.utils.time_window import get_daily_window_utc

UTC_TZ = ZoneInfo("UTC")

def normalize_football_events(day: str) -> List[Dict]:
    """
    Normaliza eventos de fútbol (fixtures) para un DÍA DE CICLO (YYYY-MM-DD).

    Reglas:
    - Solo partidos 'Not Started' (status.short == 'NS')
    - Solo eventos dentro de la ventana oficial 06:00 → 06:00 (Europe/Madrid) del ciclo
    - Lee de la verdad única: api/data/events/<day>/football.json
    - No persiste en disco
    """
    base_path = data_path("events", day)
    file_path = base_path / "football.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    window_start_utc, window_end_utc = get_daily_window_utc(day)

    normalized_events: List[Dict] = []

    for item in raw_data.get("response", []):
        fixture = item.get("fixture", {})
        league = item.get("league", {})
        teams = item.get("teams", {})
        status = fixture.get("status", {})

        # Solo partidos no empezados
        if status.get("short") != "NS":
            continue

        start_time_str = fixture.get("date")
        if not start_time_str:
            continue

        try:
            start_time_utc = datetime.fromisoformat(
                start_time_str.replace("Z", "+00:00")
            ).astimezone(UTC_TZ)
        except ValueError:
            continue

        # Ventana temporal oficial del ciclo
        if not (window_start_utc <= start_time_utc < window_end_utc):
            continue

        home_team = teams.get("home", {}).get("name")
        away_team = teams.get("away", {}).get("name")
        if not home_team or not away_team:
            continue

        normalized_events.append(
            {
                "eventId": str(fixture.get("id")),
                "sport": "football",
                "league": league.get("name"),
                "startTime": start_time_str,
                "home": home_team,
                "away": away_team,
            }
        )

    return normalized_events
