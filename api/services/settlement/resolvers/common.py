from typing import Literal

Result = Literal["WIN", "LOSS", "VOID"]


def _void_if_invalid(*values) -> bool:
    for v in values:
        if v is None:
            return True
    return False


def resolve_by_score(
    home: int | None,
    away: int | None,
    market: str,
    selection: str,
) -> Result:
    """
    Generic resolver for score-based sports.
    Supported markets:
    - home_win
    - away_win
    - draw
    """

    if _void_if_invalid(home, away):
        return "VOID"

    if market == "home_win":
        return "WIN" if home > away else "LOSS"

    if market == "away_win":
        return "WIN" if away > home else "LOSS"

    if market == "draw":
        return "WIN" if home == away else "LOSS"

    return "VOID"


def resolve_by_winner(
    winner_id: int | None,
    selection_id: int | None,
) -> Result:
    """
    Resolver for winner-only sports (tennis, mma, etc.)
    """

    if _void_if_invalid(winner_id, selection_id):
        return "VOID"

    return "WIN" if winner_id == selection_id else "LOSS"


def resolve_by_position(
    final_position: int | None,
    target_position: int,
) -> Result:
    """
    Resolver for position-based markets (F1 podium, top-N)
    """

    if _void_if_invalid(final_position):
        return "VOID"

    return "WIN" if final_position <= target_position else "LOSS"
