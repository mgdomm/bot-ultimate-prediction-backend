from .base import BaseResolver
from .common import resolve_by_score


class BasketballResolver(BaseResolver):
    sport = "basketball"

    def resolve(self, pick: dict, event: dict) -> str:
        scores = event.get("scores", {})
        return resolve_by_score(
            home=scores.get("home"),
            away=scores.get("away"),
            market=pick.get("market"),
            selection=pick.get("selection"),
        )
