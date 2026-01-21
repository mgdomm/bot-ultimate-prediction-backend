from typing import Dict, Any
from .base import BaseResolver


class TennisResolver(BaseResolver):
    sport = "tennis"

    def fetch_event(self, event_id: int) -> Dict[str, Any]:
        """
        Obtiene el evento final de tennis desde API-SPORTS.
        """
        response = self.api_client.get(
            "/tennis/events",
            params={"id": event_id}
        )
        return response["response"][0]

    def resolve_pick(self, pick: Dict[str, Any]) -> Dict[str, Any]:
        event = self.fetch_event(pick["event_id"])

        status = event.get("status")
        scores = event.get("scores", {})
        sets = scores.get("sets", {})

        home_sets = sets.get("home")
        away_sets = sets.get("away")

        # Cancelado o interrumpido sin finalizar
        if status in ("Canceled", "Interrupted"):
            return {
                "result": "VOID",
                "evidence": {
                    "status": status
                }
            }

        # Walkover o Retired → ganador declarado
        if status in ("Walkover", "Retired"):
            winner = event.get("winner")
            result = "WIN" if pick["selection"] == winner else "LOSS"
            return {
                "result": result,
                "evidence": {
                    "status": status,
                    "winner": winner
                }
            }

        # Finished
        if status == "Finished":
            if home_sets > away_sets:
                winner = "home"
            elif away_sets > home_sets:
                winner = "away"
            else:
                return {
                    "result": "VOID",
                    "evidence": {
                        "status": status,
                        "home_sets": home_sets,
                        "away_sets": away_sets
                    }
                }

            result = "WIN" if pick["selection"] == winner else "LOSS"

            return {
                "result": result,
                "evidence": {
                    "status": status,
                    "home_sets": home_sets,
                    "away_sets": away_sets
                }
            }

        # Fallback seguro
        return {
            "result": "VOID",
            "evidence": {
                "status": status
            }
        }
