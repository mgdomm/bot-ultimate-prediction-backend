import json
from itertools import combinations
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

DATA = Path(__file__).resolve().parents[1] / "data"
POOLS_DIR = DATA / "pools"

RULE = {"legs": 2, "min_odds": 1.25}
G = {
    "min_leg_probability": 0.62,
    "max_leg_odds": 2.10,
    "allowed_market_risk": {"low", "medium"},
    "min_combined_probability": 0.50,
    "min_combined_odds": 1.80,
    "max_combined_odds": 3.20,
    "min_leg_edge": 0.0,
    "min_edge_sum": 0.0,
}

def list_days():
    out=[]
    if not POOLS_DIR.exists(): return out
    for p in POOLS_DIR.iterdir():
        if p.is_dir():
            try:
                datetime.strptime(p.name, "%Y-%m-%d")
                out.append(p.name)
            except: pass
    return sorted(out)

def load(day, name):
    path = POOLS_DIR / day / f"{name}.json"
    if not path.exists():
        return path, []
    d = json.load(open(path, "r", encoding="utf-8"))
    return path, (d if isinstance(d, list) else [])

def f(x, d=0.0):
    try: return float(x)
    except: return d

def norm_mr(x): return str(x or "").strip().lower()

def leg_pass(s):
    o=f(s.get("odds"),0.0)
    p=f(s.get("probability"),0.0)
    e=f(s.get("edge"),0.0)
    mr=norm_mr(s.get("marketRisk"))
    eid=str(s.get("eventId") or "").strip()
    if o < RULE["min_odds"]: return False, "odds<min_odds"
    if o > G["max_leg_odds"]: return False, "odds>max_leg_odds"
    if p < G["min_leg_probability"]: return False, "p<min_leg_probability"
    if mr not in {x.lower() for x in G["allowed_market_risk"]}: return False, "marketRisk_not_allowed"
    if e < G["min_leg_edge"]: return False, "edge<min_leg_edge"
    if not eid: return False, "missing_eventId"
    return True, ""

def filter_pool(rows):
    kept=[]
    rej=Counter()
    for s in rows:
        if not isinstance(s, dict):
            rej["not_a_dict"] += 1
            continue
        ok, r = leg_pass(s)
        if ok: kept.append(s)
        else: rej[r] += 1
    return kept, rej

def comb(a,b):
    o=f(a.get("odds"),1.0)*f(b.get("odds"),1.0)
    p=f(a.get("probability"),0.0)*f(b.get("probability"),0.0)
    e=f(a.get("edge"),0.0)+f(b.get("edge"),0.0)
    return o,p,e

def distinct(a,b):
    return str(a.get("eventId")) != str(b.get("eventId"))

def brief(s):
    return {k: s.get(k) for k in ["sport","eventId","market","selection","odds","probability","edge","marketRisk","inflated"]}

def main():
    day = list_days()[-1]
    _, raw = load(day, "parlay_eligible")
    picks, rej = filter_pool(raw)

    print("DAY:", day)
    print("raw_parlay_eligible:", len(raw))
    print("filtered_eligible:", len(picks))
    print("per-leg rejects:", dict(rej))

    # EventId distribution
    c = Counter(str(s.get("eventId")) for s in picks)
    print("\nUNIQUE eventIds in filtered legs:", len(c))
    print("top eventIds:", c.most_common(10))

    # Pairwise diagnostic
    total_pairs = len(picks)*(len(picks)-1)//2
    reasons = Counter()
    best_by_prob = None
    best_by_edge = None
    best_by_odds = None

    # counts after each gate
    gate = defaultdict(int)

    for a,b in combinations(picks,2):
        gate["pairs_total"] += 1

        if not distinct(a,b):
            reasons["same_eventId"] += 1
            continue
        gate["pairs_distinct_event"] += 1

        o,p,e = comb(a,b)

        # Track "best" even if it fails later (to see what constraint blocks)
        cand_prob = (p, o, e, a, b)
        if best_by_prob is None or cand_prob[:3] > best_by_prob[:3]:
            best_by_prob = cand_prob

        cand_edge = (e, p, o, a, b)
        if best_by_edge is None or cand_edge[:3] > best_by_edge[:3]:
            best_by_edge = cand_edge

        cand_odds = (o, p, e, a, b)
        if best_by_odds is None or cand_odds[:3] > best_by_odds[:3]:
            best_by_odds = cand_odds

        if not (G["min_combined_odds"] <= o <= G["max_combined_odds"]):
            reasons["combined_odds_out_of_range"] += 1
            continue
        gate["pairs_pass_odds_range"] += 1

        if p < G["min_combined_probability"]:
            reasons["combined_probability_too_low"] += 1
            continue
        gate["pairs_pass_prob"] += 1

        if e < G["min_edge_sum"]:
            reasons["edge_sum_too_low"] += 1
            continue
        gate["pairs_pass_edge_sum"] += 1
        reasons["VALID"] += 1

    print("\nPAIR GATES:")
    for k in ["pairs_total","pairs_distinct_event","pairs_pass_odds_range","pairs_pass_prob","pairs_pass_edge_sum"]:
        print(f"  {k}: {gate.get(k,0)}")
    print("\nPAIR FAIL REASONS:")
    for k,v in reasons.most_common():
        print(f"  {k}: {v}")

    def show_best(label, best, keyname):
        if not best:
            print(f"\n{label}: NONE")
            return
        x1,x2,x3,a,b = best
        print(f"\n{label}: {keyname}={x1:.6f} other1={x2:.6f} other2={x3:.6f}")
        o,p,e = comb(a,b)
        print(" combined:", {"odds": round(o,4), "prob": round(p,6), "edge_sum": round(e,4)})
        print(" leg1:", brief(a))
        print(" leg2:", brief(b))

    # Best "potential" pairs (even if invalid) to see what is closest
    show_best("BEST_BY_PROB (among distinct-event pairs)", best_by_prob, "combined_prob")
    show_best("BEST_BY_EDGE (among distinct-event pairs)", best_by_edge, "edge_sum")
    show_best("BEST_BY_ODDS (among distinct-event pairs)", best_by_odds, "combined_odds")

if __name__ == "__main__":
    main()
