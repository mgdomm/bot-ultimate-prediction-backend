from typing import Dict, Any
from .base import BaseResolver


class FootballResolver(BaseResolver):
    sport = "football"

    def fetch_event(self, event_id: int) -> Dict[str, Any]:
        """
        Obtiene el evento final de football desde API-SPORTS.
        """
        response = self.api_client.get(
            "/fixtures",
            params={"id": event_id}
        )
        return response["response"][0]

    def resolve_pick(self, pick: Dict[str, Any]) -> Dict[str, Any]:
        event = self.fetch_event(pick["event_id"])

        fixture = event.get("fixture", {})
        status = fixture.get("status", {}).get("short")

        goals = event.get("goals", {})
        home_goals = goals.get("home")
        away_goals = goals.get("away")

        # Evento cancelado o no finalizado
        if status not in ("FT", "AET", "PEN"):
            return {
                "result": "VOID",
                "evidence": {
                    "status": status
                }
            }

        # Solo market: match_winner
        selection = pick["selection"]

        if home_goals > away_goals:
            winner = "home"
        elif away_goals > home_goals:
            winner = "away"
        else:
            winner = "draw"

        result = "WIN" if selection == winner else "LOSS"

        return {
            "result": result,
            "evidence": {
                "status": status,
                "home_goals": home_goals,
                "away_goals": away_goals
            }
        }
