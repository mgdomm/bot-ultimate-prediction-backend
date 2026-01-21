from pathlib import Path
import time, re, json
from itertools import combinations

FILE = Path("services/picks_parlay.py")
assert FILE.exists(), f"Not found: {FILE}"

src0 = FILE.read_text(encoding="utf-8")
bak = FILE.with_suffix(FILE.suffix + f".bak_{int(time.time())}")
bak.write_text(src0, encoding="utf-8")
print("BACKUP:", bak)

lines = src0.splitlines(True)

# ----------------------------
# A) Fix principal_2_legs guardrails block (indent + keys)
# ----------------------------
text = "".join(lines)

m = re.search(r'("principal_2_legs"\s*:\s*\{\s*\n)(.*?)(\n\s*\}\s*,\s*\n)', text, flags=re.S)
if not m:
    raise RuntimeError("No encuentro el bloque principal_2_legs dentro de PARLAY_GUARDRAILS")

header, body, tail = m.group(1), m.group(2), m.group(3)

def set_key(body: str, key: str, value_literal: str) -> str:
    # replace if exists
    if re.search(rf'^\s*"{re.escape(key)}"\s*:', body, flags=re.M):
        body = re.sub(
            rf'^(\s*"{re.escape(key)}"\s*:\s*)([^,\n]+)',
            rf'\g<1>{value_literal}',
            body,
            flags=re.M
        )
    else:
        # insert after allowed_market_risk if present, else after max_leg_odds, else at top
        ins = f'        "{key}": {value_literal},\n'
        if re.search(r'^\s*"allowed_market_risk"\s*:', body, flags=re.M):
            body = re.sub(r'(^\s*"allowed_market_risk".*\n)', r'\1' + ins, body, flags=re.M)
        elif re.search(r'^\s*"max_leg_odds"\s*:', body, flags=re.M):
            body = re.sub(r'(^\s*"max_leg_odds".*\n)', r'\1' + ins, body, flags=re.M)
        else:
            body = ins + body
    return body

# Tus decisiones de producto:
# - Regla económica
# - floor 0.40
# - margen 0.03 (premium)
# Como vimos, con el pool del 2026-01-18 no hay principal con 0.03; añadimos fallback 0.027 para no quedarte sin principal.
body = set_key(body, "min_combined_probability", "0.0")  # legacy, no manda
body = set_key(body, "min_combined_probability_floor", "0.40")
body = set_key(body, "value_margin", "0.03")
body = set_key(body, "fallback_value_margin", "0.027")  # para evitar principal: no cuando el pool no da

text = text[:m.start()] + header + body + tail + text[m.end():]

# ----------------------------
# B) Patch build_best_parlay combo probability check to economic rule (+ fallback)
# ----------------------------
lines = text.splitlines(True)

# Find where guard is read
idx_min_prob = None
for i, ln in enumerate(lines):
    if "min_combined_prob" in ln and "guard.get" in ln and "min_combined_probability" in ln:
        idx_min_prob = i
        break

if idx_min_prob is None:
    raise RuntimeError("No encuentro la línea min_combined_prob = float(guard.get('min_combined_probability', ...))")

indent = re.match(r"^(\s*)", lines[idx_min_prob]).group(1)

# Insert value_margin/prob_floor/fallback_margin right after min_combined_prob line, if not already present
need_inserts = [
    f"{indent}value_margin = float(guard.get(\"value_margin\", 0.03))\n",
    f"{indent}prob_floor = float(guard.get(\"min_combined_probability_floor\", 0.40))\n",
    f"{indent}fallback_value_margin = float(guard.get(\"fallback_value_margin\", value_margin))\n",
]

# detect existing
block_window = "".join(lines[idx_min_prob:idx_min_prob+10])
for ins in need_inserts:
    if ins.strip() not in block_window:
        lines.insert(idx_min_prob+1, ins)
        idx_min_prob += 1  # keep inserts in order

# Now patch the tot_prob check
# We locate:
#   tot_prob = combined_probability(combo_list)
#   if tot_prob < min_combined_prob:
#       continue
patched_checks = 0
for i in range(len(lines)):
    if "tot_prob" in lines[i] and "combined_probability" in lines[i]:
        # look ahead for if tot_prob < something
        j = i + 1
        while j < min(i+6, len(lines)):
            if re.search(r'^\s*if\s+tot_prob\s*<\s*min_combined_prob\s*:', lines[j]):
                # next line should be continue (maybe indented)
                k = j + 1
                # replace the if+continue with economic rule
                ind_if = re.match(r"^(\s*)", lines[j]).group(1)
                repl = []
                repl.append(f"{ind_if}# Regla económica (valor): prob >= max(floor, 1/odds + margin)\n")
                repl.append(f"{ind_if}min_required_prob = max(prob_floor, (1.0 / float(odds)) + value_margin)\n")
                repl.append(f"{ind_if}if tot_prob < max(min_combined_prob, min_required_prob):\n")
                repl.append(f"{ind_if}    continue\n")
                # overwrite j and remove the following continue line if it exists
                lines[j:j+2] = repl
                patched_checks += 1
                break
            j += 1

if patched_checks == 0:
    raise RuntimeError("No pude parchear el check tot_prob < min_combined_prob (no encontré el patrón).")

text2 = "".join(lines)
FILE.write_text(text2, encoding="utf-8")
print("PATCHED:", FILE, "patched_checks:", patched_checks)

# ----------------------------
# C) Quick validation on 2026-01-18 with your strict per-leg filters
#   We test:
#    - margin 0.03 + floor 0.40 (expected 0)
#    - fallback margin 0.027 + floor 0.40 (expected >0)
# ----------------------------
DAY = "2026-01-18"
pool = Path("data/pools")/DAY/"parlay_eligible.json"
rows = json.load(open(pool, "r", encoding="utf-8"))

MIN_ODDS=1.25; MIN_LEG_P=0.62; MAX_LEG_ODDS=2.10; ALLOWED={"low","medium"}; MIN_EDGE=0.0
MIN_CO=1.80; MAX_CO=3.20; MIN_EDGE_SUM=0.0

def f(x,d=0.0):
    try: return float(x)
    except: return d

def norm(x): return str(x or "").strip().lower()

def leg_ok(s):
    o=f(s.get("odds"),0.0); pr=f(s.get("probability"),0.0); e=f(s.get("edge"),0.0)
    if o < MIN_ODDS or o > MAX_LEG_ODDS: return False
    if pr < MIN_LEG_P: return False
    if norm(s.get("marketRisk")) not in ALLOWED: return False
    if e < MIN_EDGE: return False
    if not str(s.get("eventId") or "").strip(): return False
    return True

def distinct(a,b): return str(a.get("eventId")) != str(b.get("eventId"))
def comb_odds(a,b): return f(a.get("odds"),1.0)*f(b.get("odds"),1.0)
def comb_prob(a,b): return f(a.get("probability"),0.0)*f(b.get("probability"),0.0)
def comb_edge(a,b): return f(a.get("edge"),0.0)+f(b.get("edge"),0.0)

picks=[s for s in rows if isinstance(s,dict) and leg_ok(s)]
print("VALIDATE_DAY:", DAY, "filtered_legs:", len(picks))

def count(margin, floor):
    ok=0
    best=None
    for a,b in combinations(picks,2):
        if not distinct(a,b): continue
        o=comb_odds(a,b); pr=comb_prob(a,b); e=comb_edge(a,b)
        if o<MIN_CO or o>MAX_CO: continue
        if e<MIN_EDGE_SUM: continue
        minreq=max(floor,(1.0/o)+margin)
        if pr<minreq: continue
        ok += 1
        cand=(o,pr,e,minreq,a,b)
        if best is None or cand[:3] > best[:3]:
            best=cand
    return ok, best

def brief(s):
    return {k:s.get(k) for k in ["sport","eventId","market","selection","odds","probability","edge","marketRisk"]}

ok1,b1 = count(0.03,0.40)
print("ECON margin=0.03 floor=0.40 combos:", ok1)

ok2,b2 = count(0.027,0.40)
print("ECON fallback margin=0.027 floor=0.40 combos:", ok2)
if b2:
    o,pr,e,minreq,a,b = b2
    print("BEST_FALLBACK:", {"odds": round(o,4), "prob": round(pr,6), "minreq": round(minreq,6), "edge_sum": round(e,4)})
    print(" leg1:", brief(a))
    print(" leg2:", brief(b))
