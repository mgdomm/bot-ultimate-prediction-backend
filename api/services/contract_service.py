from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

ALLOWED_TYPES = {"classic", "parlay"}
ALLOWED_RISK = {"green", "yellow", "red"}
ALLOWED_RESULTS = {None, "win", "lose", "void"}


def _s(v: Any) -> str:
    if v is None:
        return ""
    return v if isinstance(v, str) else str(v)


def _b(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        x = v.strip().lower()
        if x in {"1", "true", "yes", "y"}:
            return True
        if x in {"0", "false", "no", "n"}:
            return False
    return False


def _f(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except Exception:
            return default
    return default


def _r2(x: float) -> float:
    try:
        return float(f"{float(x):.2f}")
    except Exception:
        return 0.0


def _risk_from_p(p: float) -> str:
    if p >= 0.65:
        return "green"
    if p >= 0.55:
        return "yellow"
    return "red"


def normalize_bet(
    bet: Dict[str, Any],
    *,
    bet_type: Optional[str] = None,
    default_stake: float = 50.0,
) -> Tuple[Dict[str, Any], List[str]]:
    errs: List[str] = []
    b = bet or {}

    t = _s(bet_type or b.get("type")).strip().lower()
    if t not in ALLOWED_TYPES:
        errs.append(f"type invalid/missing: {b.get('type')!r}")
        t = bet_type if bet_type in ALLOWED_TYPES else "classic"

    bet_id = _s(b.get("id")).strip()
    if not bet_id:
        errs.append("id missing")
        bet_id = "UNKNOWN"

    def req(key: str) -> str:
        val = _s(b.get(key)).strip()
        if val == "":
            errs.append(f"{key} missing/empty")
        return val

    title = req("title")
    sport = req("sport")
    event = req("event")
    market = req("market")
    start_time = req("startTime")
    status = req("status")

    selections = b.get("selections", [])
    if selections is None:
        selections = []
    if not isinstance(selections, list):
        errs.append("selections must be list")
        selections = []

    tp_raw = b.get("totalProbability", None)
    to_raw = b.get("totalOdds", None)
    st_raw = b.get("stake", None)

    if tp_raw is None:
        errs.append("totalProbability missing")
    if to_raw is None:
        errs.append("totalOdds missing")
    if st_raw is None:
        errs.append("stake missing")

    total_prob = _r2(max(0.0, min(1.0, _f(tp_raw, 0.0))))
    total_odds = _r2(max(0.0, _f(to_raw, 0.0)))
    stake = _r2(max(0.0, _f(st_raw, default_stake)))

    if total_odds <= 0:
        errs.append("totalOdds must be > 0")
    if stake <= 0:
        errs.append("stake must be > 0")

    pw_raw = b.get("potentialWin", None)
    if pw_raw is None:
        errs.append("potentialWin missing (derived)")
        potential_win = stake * total_odds
    else:
        potential_win = _f(pw_raw, 0.0)
    potential_win = _r2(max(0.0, potential_win))

    rl_raw = b.get("riskLevel", None)
    risk = _s(rl_raw).strip().lower()
    if risk not in ALLOWED_RISK:
        errs.append("riskLevel missing/invalid (derived)")
        risk = _risk_from_p(total_prob)

    is_premium = _b(b.get("isPremium"))
    premium_score = _r2(max(0.0, _f(b.get("premiumScore"), 0.0)))
    premium_reason = b.get("premiumReason", None)
    if premium_reason is not None and not isinstance(premium_reason, str):
        premium_reason = _s(premium_reason)

    result = b.get("result", None)
    if result is not None:
        result = _s(result).strip().lower()
    if result not in ALLOWED_RESULTS:
        errs.append(f"result invalid: {b.get('result')!r}")
        result = None

    normalized: Dict[str, Any] = {
        "id": bet_id,
        "type": t,
        "title": title,
        "sport": sport,
        "event": event,
        "market": market,
        "startTime": start_time,
        "status": status,
        "selections": selections,
        "totalProbability": total_prob,
        "totalOdds": total_odds,
        "stake": stake,
        "potentialWin": potential_win,
        "riskLevel": risk,
        "isPremium": is_premium,
        "premiumScore": premium_score,
        "premiumReason": premium_reason,
        "result": result,
    }
    return normalized, errs


def normalize_and_validate_bets(
    bets: List[Dict[str, Any]],
    *,
    bet_type: Optional[str] = None,
    strict: bool = True,
    default_stake: float = 50.0,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if bets is None:
        return [], [{"id": "LIST", "errors": ["bets list is None"]}]
    if not isinstance(bets, list):
        return [], [{"id": "LIST", "errors": ["bets must be a list"]}]

    out: List[Dict[str, Any]] = []
    detailed: List[Dict[str, Any]] = []

    for i, b in enumerate(bets):
        if not isinstance(b, dict):
            detailed.append({"id": f"INDEX_{i}", "errors": ["bet must be an object/dict"]})
            continue
        nb, errs = normalize_bet(b, bet_type=bet_type, default_stake=default_stake)
        if strict:
            if nb.get("id") == "UNKNOWN" and "id missing" not in errs:
                errs.append("id missing")
            if nb.get("type") not in ALLOWED_TYPES:
                errs.append("type invalid")
        if errs:
            detailed.append({"id": nb.get("id", f"INDEX_{i}"), "errors": errs})
        out.append(nb)

    return out, detailed
