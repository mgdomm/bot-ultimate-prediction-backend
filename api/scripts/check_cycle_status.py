import json
from pathlib import Path
from api.utils.cycle_day import cycle_day_str

day = cycle_day_str()
print("CYCLE_DAY:", day)

paths = [
    ("odds", Path(f"api/data/odds/{day}/all.json")),
    ("odds_normalized", Path(f"api/data/odds_normalized/{day}/all.json")),
    ("odds_probability", Path(f"api/data/odds_probability/{day}/all.json")),
    ("odds_estimated", Path(f"api/data/odds_estimated/{day}/all.json")),
    ("odds_ev", Path(f"api/data/odds_ev/{day}/all.json")),
    ("odds_risk", Path(f"api/data/odds_risk/{day}/all.json")),
    ("odds_premium", Path(f"api/data/odds_premium/{day}/all.json")),
    ("parlay_eligible", Path(f"api/data/pools/{day}/parlay_eligible.json")),
    ("inflated", Path(f"api/data/pools/{day}/inflated.json")),
]

print("\nCOUNTS:")
for label, p in paths:
    if not p.exists():
        print(label, "MISSING", p)
        continue
    d = json.load(open(p, "r", encoding="utf-8"))
    n = len(d) if isinstance(d, list) else "non-list"
    print(f"{label:16s} len={n} size={p.stat().st_size}")

contract = Path(f"api/data/contracts/{day}/contract.json")
print("\nCONTRACT:", contract, "exists:", contract.exists(), "size:", (contract.stat().st_size if contract.exists() else None))
if contract.exists():
    c = json.load(open(contract, "r", encoding="utf-8"))
    pc = c.get("picks_classic") or []
    pp = c.get("picks_parlay_premium") or []
    print("CONTRACT_SUMMARY:", {
        "contract_date": c.get("contract_date"),
        "generated_at": c.get("generated_at"),
        "picks_classic": len(pc),
        "picks_parlay_premium": len(pp),
    })
