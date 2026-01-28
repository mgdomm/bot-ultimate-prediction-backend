"""
Live Score Update Service
Updates existing contracts with live scores from alternative APIs (ESPN, etc)
Called every 10 minutes to keep scores fresh without regenerating picks
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import date as date_type

logger = logging.getLogger(__name__)

try:
    from services.live_events_multisource import get_live_events_for_sport
except ImportError:
    from api.services.live_events_multisource import get_live_events_for_sport


REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


def update_contract_with_live_scores(day: str) -> Dict[str, Any]:
    """
    Update existing contract with live scores
    
    1. Load contract from disk
    2. For each pick, fetch live score from alternative APIs
    3. Update contract with live data
    4. Save back to disk
    
    Returns summary of updates
    """
    contract_file = API_DATA_DIR / "contracts" / day / "contract.json"
    
    if not contract_file.exists():
        logger.info(f"Contract does not exist for {day}, skipping live update")
        return {"status": "skipped", "reason": "no_contract"}
    
    try:
        contract = json.loads(contract_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Error loading contract for {day}: {e}")
        return {"status": "error", "reason": str(e)}
    
    # Recolectar todos los IDs por deporte
    picks_by_sport = _group_picks_by_sport(contract)
    
    updates_count = 0
    errors = []
    
    # Para cada deporte, actualizar scores
    for sport, event_ids in picks_by_sport.items():
        try:
            # Fetch live events from alternative APIs
            live_events = get_live_events_for_sport(sport, event_ids)
            
            if not live_events:
                logger.debug(f"No live events found for {sport}")
                continue
            
            # Build lookup: eventId -> live_data
            live_by_id = {str(e.get("eventId", "")): e for e in live_events}
            
            # Update picks with live data
            for section in ["picks_classic", "picks_parlay_premium", "picks_value"]:
                if section not in contract or not isinstance(contract[section], list):
                    continue
                
                for pick in contract[section]:
                    event_id = str(pick.get("eventId", ""))
                    if event_id in live_by_id:
                        live_data = live_by_id[event_id]
                        
                        # Update live fields
                        pick["liveScore"] = live_data.get("liveScore")
                        pick["liveStatus"] = live_data.get("liveStatus")
                        pick["liveTime"] = live_data.get("liveTime")
                        pick["lastUpdate"] = live_data.get("timestamp")
                        
                        updates_count += 1
        
        except Exception as e:
            msg = f"Error updating {sport}: {e}"
            logger.error(msg)
            errors.append(msg)
    
    # Save updated contract
    try:
        contract_file.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"Updated contract for {day} with {updates_count} live scores")
    except Exception as e:
        logger.error(f"Error saving contract for {day}: {e}")
        return {"status": "error", "reason": f"save_failed: {e}"}
    
    return {
        "status": "success",
        "day": day,
        "updates_count": updates_count,
        "errors": errors,
    }


def _group_picks_by_sport(contract: Dict[str, Any]) -> Dict[str, List[int]]:
    """Extract event IDs grouped by sport from all pick sections"""
    picks_by_sport: Dict[str, List[int]] = {}
    
    for section in ["picks_classic", "picks_parlay_premium", "picks_value"]:
        picks = contract.get(section) or []
        if not isinstance(picks, list):
            continue
        
        for pick in picks:
            if not isinstance(pick, dict):
                continue
            
            sport = pick.get("sport", "").lower()
            event_id = pick.get("eventId")
            
            if not sport or event_id is None:
                continue
            
            if sport not in picks_by_sport:
                picks_by_sport[sport] = []
            
            if event_id not in picks_by_sport[sport]:
                picks_by_sport[sport].append(event_id)
    
    return picks_by_sport


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        day = str(date_type.today())
    else:
        day = sys.argv[1]
    
    result = update_contract_with_live_scores(day)
    print(json.dumps(result, ensure_ascii=False, indent=2))
