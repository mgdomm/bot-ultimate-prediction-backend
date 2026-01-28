import json
import sys
from pathlib import Path
from datetime import date
from itertools import combinations
from typing import List, Dict, Any, Optional, Tuple
from api.utils.paths import data_path, ensure_dir


STAKE = 50.0

PARLAY_RULES = {
    "principal_2_legs": {"legs": 2, "min_odds": 1.25, "min_profit": 0.0},
    "marketing_3_legs": {"legs": 3, "min_odds": 1.60, "min_profit": 400.0},
    "marketing_4_legs": {"legs": 4, "min_odds": 1.60, "min_profit": 800.0},
}

PARLAY_GUARDRAILS = {
    "principal_2_legs": {
        "min_leg_probability": 0.62,
        "max_leg_odds": 2.10,
        "allowed_market_risk": {"low", "medium"},

        # Regla económica (valor):
        # tot_prob >= max(floor, 1/combined_odds + margin)
        "min_combined_probability": 0.0,              # legacy/compat
        "min_combined_probability_floor": 0.40,       # floor duro
        "value_margin": 0.03,                         # premium target
        "fallback_value_margin": 0.027,               # fallback mínimo si no hay candidatos

        "min_combined_odds": 1.80,
        "max_combined_odds": 3.20,

        "min_leg_edge": 0.0,
        "min_edge_sum": 0.0,
    },
    "marketing_3_legs": {
        "min_leg_probability": 0.33,
        "max_leg_odds": 3.50,
        "allowed_market_risk": {"low", "medium", "high"},
        "min_combined_probability": 0.0,
        "min_combined_odds": 0.0,
        "max_combined_odds": 60.0,
        "min_leg_edge": None,
        "min_edge_sum": None,
    },
    "marketing_4_legs": {
        "min_leg_probability": 0.30,
        "max_leg_odds": 4.00,
        "allowed_market_risk": {"low", "medium", "high"},
        "min_combined_probability": 0.0,
        "min_combined_odds": 0.0,
        "max_combined_odds": 120.0,
        "min_leg_edge": None,
        "min_edge_sum": None,
    },
}

def combined_odds(picks: List[Dict[str, Any]]) -> float:
    result = 1.0
    for p in picks:
        try:
            result *= float(p.get("odds", 1.0) or 1.0)
        except Exception:
            result *= 1.0
    return result


def combined_probability(picks: List[Dict[str, Any]]) -> float:
    prob = 1.0
    for p in picks:
        try:
            prob *= float(p.get("probability") or 0.0)
        except Exception:
            prob *= 0.0
    return prob


def profit_from_odds(odds: float) -> float:
    return odds * STAKE - STAKE


def _consensus_rank(v: Any) -> int:
    s = str(v or "").strip().lower()
    if s == "high":
        return 2
    if s == "medium":
        return 1
    return 0


def load_pool(day: str, name: str) -> List[Dict[str, Any]]:
    path = Path(f"api/data/pools/{day}/{name}.json")
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def load_classic_selections(day: str) -> List[Dict[str, Any]]:
    base_path = Path(f"api/data/picks_classic/{day}")
    if not base_path.exists():
        return []

    selections: List[Dict[str, Any]] = []
    for file in base_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                selections.extend(data)
            elif isinstance(data, dict):
                selections.append(data)
    return selections


def base_filter_pool(selections: List[Dict[str, Any]], min_odds: float, guardrails: Dict[str, Any]) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    allowed_risk = {str(x).lower() for x in (guardrails.get("allowed_market_risk") or [])}

    min_leg_edge = guardrails.get("min_leg_edge", None)
    if min_leg_edge is not None:
        try:
            min_leg_edge = float(min_leg_edge)
        except Exception:
            min_leg_edge = None

    for s in selections:
        try:
            odds = float(s.get("odds") or 0.0)
        except Exception:
            continue
        if odds < float(min_odds):
            continue
        if odds > float(guardrails.get("max_leg_odds", 999.0)):
            continue

        try:
            p = float(s.get("probability") or 0.0)
        except Exception:
            p = 0.0
        if p < float(guardrails.get("min_leg_probability", 0.0)):
            continue

        market_risk = str(s.get("marketRisk") or "").strip().lower()
        if allowed_risk and market_risk not in allowed_risk:
            continue

        # edge por leg (si no viene, lo tratamos como 0.0)
        if min_leg_edge is not None:
            try:
                e = float(s.get("edge") or 0.0)
            except Exception:
                e = 0.0
            if e < min_leg_edge:
                continue

        event_id = s.get("eventId")
        if event_id is None or str(event_id).strip() == "":
            continue

        filtered.append(s)

    return filtered


def base_filter_classic(selections: List[Dict[str, Any]], min_odds: float) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for s in selections:
        if s.get("risk", {}).get("level") != "MEDIUM":
            continue
        if float(s.get("odds", 0) or 0) < float(min_odds):
            continue
        filtered.append(s)
    return filtered


def valid_events(picks: List[Dict[str, Any]]) -> bool:
    event_ids = {str(p.get("eventId")) for p in picks}
    return len(event_ids) == len(picks)


def build_best_parlay(selections: List[Dict[str, Any]], rule_key: str, rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    guard = PARLAY_GUARDRAILS[rule_key]

    max_combined_odds = float(guard.get("max_combined_odds", 999999.0))
    min_combined_odds = float(guard.get("min_combined_odds", 0.0))

    # legacy/compat (lo mantenemos por si se usa en marketing)
    min_combined_prob = float(guard.get("min_combined_probability", 0.0))

    # Regla económica
    value_margin = float(guard.get("value_margin", 0.03))
    prob_floor = float(guard.get("min_combined_probability_floor", 0.40))
    fallback_value_margin = float(guard.get("fallback_value_margin", value_margin))

    min_edge_sum = guard.get("min_edge_sum", None)
    if min_edge_sum is not None:
        try:
            min_edge_sum = float(min_edge_sum)
        except Exception:
            min_edge_sum = None

    def _build_candidates(margin: float) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        for combo in combinations(selections, int(rule["legs"])):
            combo_list = list(combo)
            if not valid_events(combo_list):
                continue

            odds = combined_odds(combo_list)
            if odds > max_combined_odds:
                continue
            if odds < min_combined_odds:
                continue

            tot_prob = combined_probability(combo_list)
            min_required_prob = max(prob_floor, (1.0 / float(odds)) + float(margin))
            if tot_prob < max(min_combined_prob, min_required_prob):
                continue

            profit = profit_from_odds(odds)
            if profit < float(rule["min_profit"]):
                continue

            total_edge = 0.0
            total_cons = 0
            for p in combo_list:
                try:
                    total_edge += float(p.get("edge") or 0.0)
                except Exception:
                    total_edge += 0.0
                total_cons += _consensus_rank(p.get("consensus"))

            if min_edge_sum is not None and total_edge < float(min_edge_sum):
                continue

            candidates.append({
                "picks": combo_list,
                "combined_odds": round(float(odds), 4),
                "combined_probability": round(float(tot_prob), 6),
                "stake": float(STAKE),
                "expected_profit": round(float(profit), 2),
                "expected_edge_sum": round(float(total_edge), 4),
                "consensus_score_sum": int(total_cons),
            })
        return candidates

    # 1) premium
    candidates = _build_candidates(value_margin)

    # 2) fallback mínimo si premium no da nada
    if (not candidates) and (float(fallback_value_margin) != float(value_margin)):
        candidates = _build_candidates(fallback_value_margin)

    if not candidates:
        return None

    # Principal: atractivo/odds primero; Marketing: edge primero
    if rule_key == "principal_2_legs":
        candidates.sort(
            key=lambda x: (
                x.get("combined_odds", 0.0),
                x.get("combined_probability", 0.0),
                x.get("expected_edge_sum", 0.0),
                x.get("consensus_score_sum", 0),
            ),
            reverse=True,
        )
    else:
        candidates.sort(
            key=lambda x: (
                x.get("expected_edge_sum", 0.0),
                x.get("combined_probability", 0.0),
                x.get("consensus_score_sum", 0),
                x.get("expected_profit", 0.0),
            ),
            reverse=True,
        )

    return candidates[0]

def _get_pick_id(pick: Dict[str, Any]) -> str:
    """Get unique pick identifier (sport:eventId:market:selection)"""
    sport = pick.get("sport", "")
    event_id = pick.get("eventId", "")
    market = pick.get("market", "")
    selection = pick.get("selection", "")
    return f"{sport}:{event_id}:{market}:{selection}"


def _filter_out_picks(selections: List[Dict[str, Any]], exclude_ids: set) -> List[Dict[str, Any]]:
    """Remove picks that are in the exclude set"""
    return [s for s in selections if _get_pick_id(s) not in exclude_ids]


def _try_sources_for_rule(
    day: str, 
    rule_key: str, 
    rule: Dict[str, Any],
    used_picks_ids: set = None,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Build best parlay for a rule, excluding picks already used in other parlays.
    This implements DF_PARLAY_NO_DUPLICATION (A+B strategy):
    - Exclude picks from 4-legs when building 3-legs/2-legs
    - Also try alternative picks with similar EV if top choice has conflicts
    """
    if used_picks_ids is None:
        used_picks_ids = set()
    
    guard = PARLAY_GUARDRAILS[rule_key]

    inflated = load_pool(day, "inflated")
    eligible = load_pool(day, "parlay_eligible")

    if inflated or eligible:
        # Remove used picks from pools
        infl_filtered = _filter_out_picks(inflated, used_picks_ids)
        elig_filtered = _filter_out_picks(eligible, used_picks_ids)
        
        infl_f = base_filter_pool(infl_filtered, rule["min_odds"], guard)
        p = build_best_parlay(infl_f, rule_key, rule)
        if p:
            return p, "inflated"

        elig_f = base_filter_pool(elig_filtered, rule["min_odds"], guard)
        p = build_best_parlay(elig_f, rule_key, rule)
        if p:
            return p, "parlay_eligible"

        return None, "pool_no_match"

    classic = load_classic_selections(day)
    # Remove used picks from classic selections
    classic_filtered = _filter_out_picks(classic, used_picks_ids)
    classic_f = base_filter_classic(classic_filtered, rule["min_odds"])
    p = build_best_parlay(classic_f, rule_key, rule)
    return p, "classic"


def run(day: str) -> None:
    """
    DF_PARLAY_NO_DUPLICATION: Generate parlays while avoiding repetition.
    
    Order: 4-legs first (marketing_4), then 3-legs (marketing_3), then 2-legs (principal)
    Each uses picks NOT in previous ones.
    """
    used_picks_ids = set()
    marketing_parlays: List[Dict[str, Any]] = []
    
    # 1) 4-legs first (highest risk, most picks used)
    parlay_4, source_4 = _try_sources_for_rule(day, "marketing_4_legs", PARLAY_RULES["marketing_4_legs"], used_picks_ids)
    if parlay_4:
        parlay_4["type"] = "marketing_4_legs"
        parlay_4["day"] = day
        parlay_4["source"] = source_4
        marketing_parlays.append(parlay_4)
        # Mark 4-leg picks as used
        for pick in parlay_4.get("picks", []):
            used_picks_ids.add(_get_pick_id(pick))

    # 2) 3-legs (excluding 4-leg picks)
    parlay_3, source_3 = _try_sources_for_rule(day, "marketing_3_legs", PARLAY_RULES["marketing_3_legs"], used_picks_ids)
    if parlay_3:
        parlay_3["type"] = "marketing_3_legs"
        parlay_3["day"] = day
        parlay_3["source"] = source_3
        marketing_parlays.append(parlay_3)
        # Mark 3-leg picks as used
        for pick in parlay_3.get("picks", []):
            used_picks_ids.add(_get_pick_id(pick))
    
    # 3) 2-legs principal (excluding 4-leg and 3-leg picks)
    principal, principal_source = _try_sources_for_rule(day, "principal_2_legs", PARLAY_RULES["principal_2_legs"], used_picks_ids)
    if principal:
        principal["type"] = "principal_2_legs"
        principal["day"] = day
        principal["source"] = principal_source

        featured_path = Path(f"api/data/picks_parlay_featured/{day}")
        featured_path.mkdir(parents=True, exist_ok=True)
        with open(featured_path / "featured_parlay.json", "w", encoding="utf-8") as f:
            json.dump(principal, f, ensure_ascii=False, indent=2)

    output_path = Path(f"api/data/picks_parlay/{day}")
    output_path.mkdir(parents=True, exist_ok=True)
    with open(output_path / "parlays.json", "w", encoding="utf-8") as f:
        json.dump({"parlays": marketing_parlays}, f, ensure_ascii=False, indent=2)

    print(
        f"✅ Parlays generados ({day}) — "
        f"principal: {'sí' if principal else 'no'}, "
        f"marketing 4-legs: {'sí' if parlay_4 else 'no'}, "
        f"marketing 3-legs: {'sí' if parlay_3 else 'no'}"
    )


if __name__ == "__main__":
    day = sys.argv[1] if len(sys.argv) >= 2 else date.today().isoformat()
    run(day)
