from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Optional


def _day_from_bet(b: Dict) -> Optional[str]:
    """
    Deriva YYYY-MM-DD desde startTime (ISO). Esto evita depender de 'date' (no está en el contrato).
    """
    st = b.get("startTime")
    if not isinstance(st, str) or len(st) < 10:
        return None

    # Caso ISO típico: "2026-01-16T18:41:12.285921" o "2026-01-16T..."
    day = st[:10]
    if len(day) == 10 and day[4] == "-" and day[7] == "-":
        return day

    # Fallback: intentar parseo flexible (por si viene con Z u otro formato)
    try:
        dt = datetime.fromisoformat(st.replace("Z", "+00:00"))
        return dt.date().isoformat()
    except Exception:
        return None


def calculate_roi(bets: List[Dict]) -> float:
    stake = sum(float(b.get("stake", 0) or 0) for b in bets)
    if stake <= 0:
        return 0.0

    # payout (retorno):
    # - win  => potentialWin
    # - void => stake (devuelto)
    # - lose/None => 0
    returns = 0.0
    for b in bets:
        r = b.get("result")
        if r == "win":
            returns += float(b.get("potentialWin", 0) or 0)
        elif r == "void":
            returns += float(b.get("stake", 0) or 0)

    return round((returns - stake) / stake * 100, 2)


def win_rate(bets: List[Dict]) -> float:
    if not bets:
        return 0.0
    wins = sum(1 for b in bets if b.get("result") == "win")
    return round(wins / len(bets) * 100, 2)


def current_streak(bets: List[Dict]) -> int:
    streak = 0
    for bet in reversed(bets):
        if bet.get("result") == "win":
            streak += 1
        else:
            break
    return streak


def best_and_worst_days(bets: List[Dict]):
    by_day = defaultdict(list)

    for b in bets:
        day = _day_from_bet(b)
        if day is None:
            continue
        by_day[day].append(b)

    day_results = {d: calculate_roi(day_bets) for d, day_bets in by_day.items()}

    if not day_results:
        return None, None

    best = max(day_results, key=day_results.get)
    worst = min(day_results, key=day_results.get)
    return best, worst


def distribution_by_sport(bets: List[Dict]):
    dist = defaultdict(lambda: {"bets": 0, "wins": 0})

    for b in bets:
        sport = b.get("sport", "unknown")
        dist[sport]["bets"] += 1
        if b.get("result") == "win":
            dist[sport]["wins"] += 1

    return {
        sport: {
            "bets": v["bets"],
            "winRate": round(v["wins"] / v["bets"] * 100, 2) if v["bets"] else 0,
        }
        for sport, v in dist.items()
    }
