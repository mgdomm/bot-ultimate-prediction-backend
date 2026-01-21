import json, os
from itertools import combinations
from pathlib import Path
from datetime import datetime

DATA = Path(__file__).resolve().parents[1] / "data"
POOLS_DIR = DATA / "pools"

# Baseline (lo que estabas usando en el diagnóstico)
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
    if not POOLS_DIR.exists():
        return []
    out=[]
    for p in POOLS_DIR.iterdir():
        if p.is_dir():
            try:
                datetime.strptime(p.name, "%Y-%m-%d")
                out.append(p.name)
            except:
                pass
    return sorted(out)

def load(day, name):
    path = POOLS_DIR / day / f"{name}.json"
    if not path.exists():
        return path, []
    try:
        d = json.load(open(path, "r", encoding="utf-8"))
        return path, (d if isinstance(d, list) else [])
    except Exception:
        return path, []

def as_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default

def norm_mr(x):
    return str(x or "").strip().lower()

def leg_pass(s, rule, g):
    o = as_float(s.get("odds"), 0.0)
    p = as_float(s.get("probability"), 0.0)
    e = as_float(s.get("edge"), 0.0)
    mr = norm_mr(s.get("marketRisk"))
    eid = str(s.get("eventId") or "").strip()

    if o < rule["min_odds"]: return False, "odds<min_odds"
    if o > g["max_leg_odds"]: return False, "odds>max_leg_odds"
    if p < g["min_leg_probability"]: return False, "p<min_leg_probability"
    if mr not in {x.lower() for x in g["allowed_market_risk"]}: return False, "marketRisk_not_allowed"
    if e < g["min_leg_edge"]: return False, "edge<min_leg_edge"
    if not eid: return False, "missing_eventId"
    return True, ""

def filter_pool(rows, rule, g):
    kept=[]
    reasons={}
    ex={}
    for s in rows:
        if not isinstance(s, dict): 
            reasons["not_a_dict"] = reasons.get("not_a_dict", 0) + 1
            continue
        ok, r = leg_pass(s, rule, g)
        if ok:
            kept.append(s)
        else:
            reasons[r]=reasons.get(r,0)+1
            if r not in ex:
                ex[r] = {k: s.get(k) for k in ["sport","eventId","market","selection","odds","probability","edge","marketRisk","inflated"]}
    return kept, reasons, ex

def comb_odds(a,b): return as_float(a.get("odds"),1.0) * as_float(b.get("odds"),1.0)
def comb_prob(a,b): return as_float(a.get("probability"),0.0) * as_float(b.get("probability"),0.0)
def comb_edge(a,b): return as_float(a.get("edge"),0.0) + as_float(b.get("edge"),0.0)
def distinct(a,b): return str(a.get("eventId")) != str(b.get("eventId"))

def count_valid(picks, g):
    ok=0
    best=None
    for a,b in combinations(picks,2):
        if not distinct(a,b): 
            continue
        o=comb_odds(a,b); p=comb_prob(a,b); e=comb_edge(a,b)
        if o < g["min_combined_odds"] or o > g["max_combined_odds"]: 
            continue
        if p < g["min_combined_probability"]: 
            continue
        if e < g["min_edge_sum"]: 
            continue
        ok += 1
        cand=(o,p,e,a,b)
        if best is None or cand[:3] > best[:3]:
            best=cand
    return ok, best

def show_best(best, label):
    if not best:
        print(label, "best: NONE")
        return
    o,p,e,a,b = best
    print(label, "best:", {"combined_odds": round(o,4), "combined_probability": round(p,6), "edge_sum": round(e,4)})
    for i,leg in enumerate([a,b], start=1):
        print(f" leg{i}:", {k: leg.get(k) for k in ["sport","eventId","market","selection","odds","probability","edge","marketRisk","inflated"]})

def write_snapshot_csv(day, raw_elig):
    import csv
    out = Path("reports") / f"df_snapshot_{day}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["sport","eventId","market","selection","odds","probability","edge","marketRisk","inflated"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in raw_elig:
            if isinstance(s, dict):
                w.writerow({c: s.get(c) for c in cols})
    print("WROTE_SNAPSHOT:", str(out), "rows:", len(raw_elig))

def try_single_relaxations(raw_elig):
    # Solo relajamos UNA cosa a la vez para encontrar la restricción bloqueante real.
    base_rule = dict(RULE)
    base_g = dict(G)

    trials = []

    # 1) edge (normalmente es el killer, porque sample0 tenía edge=-0.08)
    for thr in [0.0, -0.01, -0.02, -0.05, -0.08, -0.10, -0.15]:
        g = dict(base_g); g["min_leg_edge"] = thr
        picks,_,_ = filter_pool(raw_elig, base_rule, g)
        ok,_ = count_valid(picks, g)
        trials.append(("min_leg_edge", thr, len(picks), ok))

    # 2) min_odds
    for mo in [1.25, 1.22, 1.20, 1.18, 1.15]:
        rule = dict(base_rule); rule["min_odds"] = mo
        picks,_,_ = filter_pool(raw_elig, rule, base_g)
        ok,_ = count_valid(picks, base_g)
        trials.append(("min_odds", mo, len(picks), ok))

    # 3) min_leg_probability
    for mp in [0.62, 0.60, 0.58, 0.55]:
        g = dict(base_g); g["min_leg_probability"] = mp
        picks,_,_ = filter_pool(raw_elig, base_rule, g)
        ok,_ = count_valid(picks, g)
        trials.append(("min_leg_probability", mp, len(picks), ok))

    # 4) allowed_market_risk include high
    g = dict(base_g); g["allowed_market_risk"] = {"low","medium","high"}
    picks,_,_ = filter_pool(raw_elig, base_rule, g)
    ok,_ = count_valid(picks, g)
    trials.append(("allowed_market_risk", "low+medium+high", len(picks), ok))

    # Orden: preferimos el primer cambio que genere >=1 combo,
    # con una heurística de "menos invasivo" según este orden:
    order = {"min_leg_edge": 0, "min_odds": 1, "min_leg_probability": 2, "allowed_market_risk": 3}
    good = [t for t in trials if t[3] > 0]
    good.sort(key=lambda t: (order.get(t[0], 99), abs((t[1] if isinstance(t[1], (int,float)) else 0)), -t[3], -t[2]))
    return trials, (good[0] if good else None)

def main():
    days = list_days()
    print("POOLS_DIR:", POOLS_DIR)
    print("days:", days[-10:])

    day = (days[-1] if days else None)
    if not day:
        print("ERROR: no pool days found in", POOLS_DIR)
        return

    pinfl, raw_infl = load(day, "inflated")
    pelig, raw_elig = load(day, "parlay_eligible")

    print("\nFILES:")
    print(" inflated:", pinfl, "exists:", pinfl.exists(), "raw:", len(raw_infl))
    print(" eligible:", pelig, "exists:", pelig.exists(), "raw:", len(raw_elig))

    # DF snapshot (CSV)
    write_snapshot_csv(day, raw_elig)

    infl, infl_reasons, infl_ex = filter_pool(raw_infl, RULE, G)
    elig, elig_reasons, elig_ex = filter_pool(raw_elig, RULE, G)

    print("\nBASELINE FILTERED (per-leg):")
    print(" filtered_inflated:", len(infl))
    print(" filtered_eligible:", len(elig))

    def pr(title, reasons, ex):
        print("\n" + title)
        if not reasons:
            print("  (no rejects)")
            return
        for k,v in sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {k}: {v} example={ex.get(k)}")

    pr("INFLATED rejects", infl_reasons, infl_ex)
    pr("ELIGIBLE rejects", elig_reasons, elig_ex)

    ok_infl, best_infl = count_valid(infl, G)
    ok_elig, best_elig = count_valid(elig, G)

    print("\nVALID COMBOS (baseline constraints):")
    print(" valid_combos_inflated:", ok_infl)
    print(" valid_combos_eligible:", ok_elig)
    show_best(best_infl, "INFLATED")
    show_best(best_elig, "ELIGIBLE")

    print("\nSINGLE-RELAXATION SEARCH (on parlay_eligible raw):")
    trials, best = try_single_relaxations(raw_elig)
    for t in trials:
        name,val,nlegs,ncomb = t
        print(f"  relax {name} -> {val}: legs={nlegs} combos={ncomb}")
    print("\nBEST_SINGLE_RELAXATION:", best)

    if len(elig) == 0:
        print("\nROOT CAUSE (baseline): per-leg filter leaves 0 legs. Check top reject reason above; sample0 already shows odds=1.22 (<1.25) and edge=-0.08 (<0).")

if __name__ == "__main__":
    main()
