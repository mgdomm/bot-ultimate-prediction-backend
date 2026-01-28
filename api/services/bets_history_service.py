"""
DF_BETS_HISTORY: Persist bet configurations with final outcomes (WIN/LOSE/PENDING)

Each day, after bets are finalized, store the contract snapshot with:
- picks_classic with final outcomes
- picks_parlay_premium with final outcomes
- timestamps and final scores
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from api.utils.cycle_day import cycle_day_str


def _outcome_for_pick(live: Dict[str, Any], market: Optional[str], selection: Optional[str]) -> Optional[str]:
    """Determine WIN/LOSE from final score and market selection"""
    if not isinstance(live, dict):
        return None
    
    status_short = str(live.get("statusShort", "") or live.get("status", "")).upper()
    if not (status_short in ("FT", "AET", "PEN", "FINAL")):
        return None
    
    home_score = live.get("homeScore")
    away_score = live.get("awayScore")
    
    if home_score is None or away_score is None:
        return None
    
    try:
        h = float(home_score)
        a = float(away_score)
    except (ValueError, TypeError):
        return None
    
    market_str = str(market or "").lower()
    selection_str = str(selection or "").lower()
    
    # Over/Under markets
    if "over" in market_str or "under" in market_str or "total" in market_str:
        import re
        mm = re.search(r'(over|under)\s*(\d+(?:\.\d+)?)', selection_str, re.I)
        if mm:
            direction = mm.group(1).lower()
            threshold = float(mm.group(2))
            total = h + a
            
            if direction == "over":
                return "WIN" if total > threshold else "LOSE"
            else:  # under
                return "WIN" if total < threshold else "LOSE"
    
    # Home/Away (1X2) markets
    if "1x2" in market_str or "result" in market_str:
        if "home" in selection_str or "1" in selection_str:
            return "WIN" if h > a else "LOSE"
        elif "away" in selection_str or "2" in selection_str:
            return "WIN" if a > h else "LOSE"
        elif "draw" in selection_str or "x" in selection_str:
            return "WIN" if h == a else "LOSE"
    
    # Handicap markets (simplified)
    if "handicap" in market_str or "spread" in market_str:
        import re
        mm = re.search(r'(home|away|1|2)\s*([+-]\d+(?:\.\d+)?)', selection_str, re.I)
        if mm:
            team = mm.group(1).lower()
            handicap = float(mm.group(2))
            if "home" in team or team == "1":
                adjusted = h + handicap
                return "WIN" if adjusted > a else "LOSE"
            else:
                adjusted = a + handicap
                return "WIN" if adjusted > h else "LOSE"
    
    return None


def archive_day_bets(contract: Dict[str, Any], day: str = None) -> None:
    """Archive today's contract with outcome evaluations"""
    if day is None:
        day = cycle_day_str()
    
    archived = dict(contract)
    archived["archived_at"] = datetime.utcnow().isoformat()
    archived["archive_day"] = day
    
    # Evaluate picks_classic outcomes
    classic_picks = archived.get("picks_classic", [])
    if isinstance(classic_picks, list):
        evaluated_classic = []
        for container in classic_picks:
            if isinstance(container, list):
                for pick in container:
                    if isinstance(pick, dict):
                        live = pick.get("display", {}).get("live")
                        outcome = _outcome_for_pick(live, pick.get("market"), pick.get("selection"))
                        pick_with_outcome = dict(pick)
                        pick_with_outcome["outcome"] = outcome
                        evaluated_classic.append(pick_with_outcome)
            elif isinstance(container, dict):
                live = container.get("display", {}).get("live")
                outcome = _outcome_for_pick(live, container.get("market"), container.get("selection"))
                pick_with_outcome = dict(container)
                pick_with_outcome["outcome"] = outcome
                evaluated_classic.append(pick_with_outcome)
        archived["picks_classic"] = evaluated_classic
    
    # Evaluate picks_parlay_premium outcomes
    parlay_premium = archived.get("picks_parlay_premium", [])
    if isinstance(parlay_premium, list):
        evaluated_parlays = []
        for parlay in parlay_premium:
            if isinstance(parlay, dict):
                parlay_with_outcomes = dict(parlay)
                legs = parlay.get("legs", [])
                if isinstance(legs, list):
                    outcomes = []
                    for leg in legs:
                        if isinstance(leg, dict):
                            live = leg.get("display", {}).get("live")
                            outcome = _outcome_for_pick(live, leg.get("market"), leg.get("selection"))
                            outcomes.append(outcome)
                    
                    # Parlay outcome: WIN if all legs WIN, LOSE if any LOSE, PENDING otherwise
                    if outcomes and all(o == "WIN" for o in outcomes):
                        parlay_outcome = "WIN"
                    elif outcomes and any(o == "LOSE" for o in outcomes):
                        parlay_outcome = "LOSE"
                    else:
                        parlay_outcome = "PENDING"
                    
                    parlay_with_outcomes["outcome"] = parlay_outcome
                    parlay_with_outcomes["leg_outcomes"] = outcomes
                
                evaluated_parlays.append(parlay_with_outcomes)
        archived["picks_parlay_premium"] = evaluated_parlays
    
    # Evaluate featured parlay
    featured = archived.get("daily_featured_parlay")
    if isinstance(featured, dict):
        featured_with_outcomes = dict(featured)
        legs = featured.get("legs", [])
        if isinstance(legs, list):
            outcomes = []
            for leg in legs:
                if isinstance(leg, dict):
                    live = leg.get("display", {}).get("live")
                    outcome = _outcome_for_pick(live, leg.get("market"), leg.get("selection"))
                    outcomes.append(outcome)
            
            if outcomes and all(o == "WIN" for o in outcomes):
                featured_outcome = "WIN"
            elif outcomes and any(o == "LOSE" for o in outcomes):
                featured_outcome = "LOSE"
            else:
                featured_outcome = "PENDING"
            
            featured_with_outcomes["outcome"] = featured_outcome
            featured_with_outcomes["leg_outcomes"] = outcomes
        
        archived["daily_featured_parlay"] = featured_with_outcomes
    
    # Persist archive
    archive_path = Path(f"api/data/contracts/{day}/archive.json")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with open(archive_path, "w", encoding="utf-8") as f:
        json.dump(archived, f, ensure_ascii=False, indent=2)


def load_day_history(day: str) -> Optional[Dict[str, Any]]:
    """Load archived bets for a specific day"""
    archive_path = Path(f"api/data/contracts/{day}/archive.json")
    if not archive_path.exists():
        return None
    
    try:
        with open(archive_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_history_days(limit: int = 30) -> List[Dict[str, Any]]:
    """List recent days with archived bets (most recent first)"""
    contracts_dir = Path("api/data/contracts")
    if not contracts_dir.exists():
        return []
    
    days_with_archives = []
    for day_dir in sorted(contracts_dir.iterdir(), reverse=True):
        if not day_dir.is_dir():
            continue
        archive_file = day_dir / "archive.json"
        if archive_file.exists():
            try:
                with open(archive_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    day_str = day_dir.name
                    
                    # Count outcomes
                    classic = data.get("picks_classic", [])
                    classic_wins = sum(1 for p in classic if isinstance(p, dict) and p.get("outcome") == "WIN")
                    classic_total = len([p for p in classic if isinstance(p, dict)])
                    
                    parlays = data.get("picks_parlay_premium", [])
                    parlay_wins = sum(1 for p in parlays if isinstance(p, dict) and p.get("outcome") == "WIN")
                    parlay_total = len([p for p in parlays if isinstance(p, dict)])
                    
                    days_with_archives.append({
                        "day": day_str,
                        "archived_at": data.get("archived_at"),
                        "classic_wins": classic_wins,
                        "classic_total": classic_total,
                        "parlay_wins": parlay_wins,
                        "parlay_total": parlay_total,
                    })
            except Exception:
                pass
            
            if len(days_with_archives) >= limit:
                break
    
    return days_with_archives
