"""
Generate demo data for future dates with realistic events and picks
Used to populate the system with test data for demonstration
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, date as date_type
from typing import Dict, List, Any

# Import robusto
try:
    from api.utils.cycle_day import cycle_day_str
    from api.utils.paths import data_path, ensure_dir
    from api.services.contract_service import create_empty_contract, populate_contract_with_day_data, freeze_and_save_contract
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from api.utils.cycle_day import cycle_day_str
    from api.utils.paths import data_path, ensure_dir
    from api.services.contract_service import create_empty_contract, populate_contract_with_day_data, freeze_and_save_contract

def generate_demo_events(day: str) -> Dict[str, Any]:
    """Generate demo events for a given day"""
    # Parse day
    from datetime import datetime
    day_dt = datetime.fromisoformat(day)
    
    events_by_sport = {
        "basketball": [
            {
                "eventId": f"bk_1_{day}",
                "sport": "basketball",
                "home": "Lakers",
                "away": "Celtics",
                "startTime": (day_dt + timedelta(hours=20)).isoformat(),
                "status": "scheduled",
                "homeOdds": 1.95,
                "awayOdds": 1.90,
                "overUnder": 220.5,
            },
            {
                "eventId": f"bk_2_{day}",
                "sport": "basketball",
                "home": "Warriors",
                "away": "Nuggets",
                "startTime": (day_dt + timedelta(hours=22)).isoformat(),
                "status": "scheduled",
                "homeOdds": 2.10,
                "awayOdds": 1.73,
                "overUnder": 219.0,
            },
        ],
        "football": [
            {
                "eventId": f"fb_1_{day}",
                "sport": "football",
                "home": "Manchester United",
                "away": "Liverpool",
                "startTime": (day_dt + timedelta(hours=19)).isoformat(),
                "status": "scheduled",
                "homeOdds": 2.40,
                "awayOdds": 1.60,
                "overUnder": 2.5,
            },
        ],
        "nfl": [
            {
                "eventId": f"nfl_1_{day}",
                "sport": "nfl",
                "home": "Chiefs",
                "away": "49ers",
                "startTime": (day_dt + timedelta(hours=18)).isoformat(),
                "status": "scheduled",
                "homeOdds": 1.85,
                "awayOdds": 2.00,
                "overUnder": 46.5,
            },
        ],
        "hockey": [
            {
                "eventId": f"hk_1_{day}",
                "sport": "hockey",
                "home": "Maple Leafs",
                "away": "Hurricanes",
                "startTime": (day_dt + timedelta(hours=21)).isoformat(),
                "status": "scheduled",
                "homeOdds": 1.90,
                "awayOdds": 1.95,
                "overUnder": 5.5,
            },
        ],
    }
    
    return events_by_sport

def save_demo_events(day: str):
    """Save demo events to disk"""
    events_by_sport = generate_demo_events(day)
    events_dir = data_path("events", day)
    ensure_dir(events_dir)
    
    for sport, events in events_by_sport.items():
        file_path = events_dir / f"{sport}.json"
        # Convert to API format
        api_format = {
            "results": len(events),
            "response": events,
            "source": "demo",
            "status": "demo_data"
        }
        file_path.write_text(json.dumps(api_format, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Generated {len(events)} demo events for {sport} on {day}")

def generate_demo_picks(day: str) -> List[Dict[str, Any]]:
    """Generate demo picks for a given day"""
    events_by_sport = generate_demo_events(day)
    picks = []
    
    for sport, events in events_by_sport.items():
        for event in events[:2]:  # Take first 2 events per sport
            picks.append({
                "sport": sport,
                "eventId": event["eventId"],
                "bookmaker": "DemoBook",
                "market": "Spread",
                "selection": "Home Team",
                "odds": event.get("homeOdds", 1.90),
                "p_implied": 1 / event.get("homeOdds", 1.90),
                "p_estimated": 1 / (event.get("homeOdds", 1.90) * 0.95),
                "stake": 50.0,
                "ev": 1.2,
                "risk": {
                    "level": "LOW",
                    "p_est": 1 / (event.get("homeOdds", 1.90) * 0.95),
                    "delta_p": 0.02,
                    "ev_margin": 0.05
                },
                "premium": True,
                "premium_reason": "DEMO_DATA"
            })
    
    return picks

def save_demo_picks(day: str):
    """Save demo picks to disk"""
    picks = generate_demo_picks(day)
    
    # Save classic picks
    picks_classic_dir = data_path("picks_classic", day)
    ensure_dir(picks_classic_dir)
    picks_file = picks_classic_dir / "all.json"
    picks_file.write_text(json.dumps(picks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Generated {len(picks)} demo classic picks for {day}")
    
    # Save parlay picks (empty for now)
    picks_parlay_dir = data_path("picks_parlay", day)
    ensure_dir(picks_parlay_dir)
    parlay_file = picks_parlay_dir / "parlays.json"
    parlay_file.write_text(json.dumps({"parlays": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Generated 0 demo parlay picks for {day}")

def generate_demo_contract(day: str):
    """Generate complete demo contract for a day"""
    save_demo_events(day)
    save_demo_picks(day)
    
    # Generate and freeze contract
    contract = create_empty_contract(day)
    contract = populate_contract_with_day_data(contract)
    contract = freeze_and_save_contract(contract)
    
    print(f"✅ Generated complete demo contract for {day}")
    print(f"   - Classic picks: {len(contract.get('picks_classic', []))}")
    print(f"   - Parlay picks: {len(contract.get('picks_parlay_premium', []))}")

def main():
    # Generate demo data for next 3 days
    today = cycle_day_str()
    today_dt = datetime.fromisoformat(today)
    
    print(f"📅 Today (cycle_day): {today}")
    print(f"🔧 Generating demo data for next 3 days...\n")
    
    for i in range(1, 4):
        future_day = (today_dt + timedelta(days=i)).date().isoformat()
        try:
            generate_demo_contract(future_day)
        except Exception as e:
            print(f"❌ Error generating demo data for {future_day}: {e}")
    
    print(f"\n✅ Demo data generation complete!")

if __name__ == "__main__":
    main()
