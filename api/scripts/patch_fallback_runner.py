from pathlib import Path
import re, time

FILE = Path("services/picks_parlay.py")
src0 = FILE.read_text(encoding="utf-8")
bak = FILE.with_suffix(FILE.suffix + f".bak_{int(time.time())}")
bak.write_text(src0, encoding="utf-8")
print("BACKUP:", bak)

src = src0

# -----------------------------
# 1) Fix principal_2_legs guardrails block (replace whole block safely)
# -----------------------------
m = re.search(r'("principal_2_legs"\s*:\s*\{\s*\n)(.*?)(\n\s*\}\s*,\s*\n)', src, flags=re.S)
if not m:
    raise RuntimeError("No encuentro el bloque principal_2_legs en PARLAY_GUARDRAILS")

old_body = m.group(2)

def get_val(key, default_literal):
    mm = re.search(rf'^\s*"{re.escape(key)}"\s*:\s*([^,\n]+)', old_body, flags=re.M)
    return mm.group(1).strip() if mm else default_literal

# preservamos tus valores existentes si estaban
min_leg_probability = get_val("min_leg_probability", "0.62")
max_leg_odds = get_val("max_leg_odds", "2.10")
allowed_market_risk = get_val("allowed_market_risk", '{"low", "medium"}')
min_combined_odds = get_val("min_combined_odds", "1.80")
max_combined_odds = get_val("max_combined_odds", "3.20")
min_leg_edge = get_val("min_leg_edge", "0.0")
min_edge_sum = get_val("min_edge_sum", "0.0")

# decisiones de producto:
# - regla económica
# - floor 0.40
# - margin premium 0.03
# - fallback mínimo 0.027 para no quedarte sin principal
new_block = (
    '"principal_2_legs": {\n'
    f'        "min_leg_probability": {min_leg_probability},\n'
    f'        "max_leg_odds": {max_leg_odds},\n'
    f'        "allowed_market_risk": {allowed_market_risk},\n'
    f'        "min_combined_probability": 0.0,\n'
    f'        "min_combined_probability_floor": 0.40,\n'
    f'        "value_margin": 0.03,\n'
    f'        "fallback_value_margin": 0.027,\n'
    f'        "min_combined_odds": {min_combined_odds},\n'
    f'        "max_combined_odds": {max_combined_odds},\n'
    f'        "min_leg_edge": {min_leg_edge},\n'
    f'        "min_edge_sum": {min_edge_sum},\n'
    '    },\n'
)

src = src[:m.start()] + new_block + src[m.end():]

# -----------------------------
# 2) Implement fallback runner inside build_best_parlay
#    Replace the existing loop "for combo in combinations(...)" block with helper+2 passes
# -----------------------------
lines = src.splitlines(True)

# find build_best_parlay start
i_build = None
for i,l in enumerate(lines):
    if l.startswith("def build_best_parlay"):
        i_build = i
        break
if i_build is None:
    raise RuntimeError("No encuentro def build_best_parlay")

# find loop start inside build_best_parlay
i_loop = None
for i in range(i_build, len(lines)):
    if re.match(r'^\s*for\s+combo\s+in\s+combinations\(', lines[i]):
        i_loop = i
        break
if i_loop is None:
    raise RuntimeError("No encuentro el for combo in combinations(...) dentro de build_best_parlay")

# find loop end: before sorting block (Principal:)
i_sort = None
for i in range(i_loop, len(lines)):
    if re.search(r'^\s*#\s*Principal:', lines[i]) or re.search(r'^\s*if\s+rule_key\s*==\s*[\'"]principal_2_legs[\'"]\s*:', lines[i]):
        i_sort = i
        break
if i_sort is None:
    raise RuntimeError("No encuentro el bloque de ordenación (Principal:) para delimitar el fin del loop")

loop_lines = lines[i_loop:i_sort]

# We will build a helper function with same content but margin parameterized
indent_loop = re.match(r"^(\s*)", lines[i_loop]).group(1)        # likely 4 spaces
indent_fn = indent_loop                                           # helper at same indent as loop
indent_in = indent_loop + "    "                                  # inside helper

# Patch the loop body: replace "+ value_margin" with "+ _margin"
patched_loop = []
for ln in loop_lines:
    patched_loop.append(ln.replace("+ value_margin", "+ _margin"))

helper = []
helper.append(f"{indent_fn}def _build_candidates(_margin: float):\n")
helper.append(f"{indent_in}candidates_local = []\n")
# rewrite first line "for combo in combinations(...)" to be inside helper
first = patched_loop[0]
helper.append(indent_in + first.lstrip())  # "for combo in combinations..." with indent
for ln in patched_loop[1:]:
    # indent every original line by 4 spaces (move into helper)
    helper.append(indent_in + ln.lstrip())
# at the end return
helper.append(f"{indent_in}return candidates_local\n")

# Now we must ensure the code uses candidates_local instead of candidates.append inside helper.
# So replace within helper any "candidates.append(" with "candidates_local.append("
helper_text = "".join(helper).replace("candidates.append(", "candidates_local.append(")

runner = []
runner.append(f"\n{indent_fn}# Ejecuta regla económica premium; si no hay candidatos, aplica fallback mínimo.\n")
runner.append(f"{indent_fn}candidates = _build_candidates(value_margin)\n")
runner.append(f"{indent_fn}if (not candidates) and (fallback_value_margin is not None) and (float(fallback_value_margin) != float(value_margin)):\n")
runner.append(f"{indent_fn}    candidates = _build_candidates(float(fallback_value_margin))\n\n")

# Replace old loop with helper + runner
lines[i_loop:i_sort] = [helper_text] + runner

out = "".join(lines)
FILE.write_text(out, encoding="utf-8")
print("PATCHED:", FILE)

# -----------------------------
# 3) Print verification snippets
# -----------------------------
txt = FILE.read_text(encoding="utf-8").splitlines()
def show(needle, radius=8, max_hits=3):
    hits = [i for i,l in enumerate(txt, start=1) if needle in l]
    print(f"\nNEEDLE={needle!r} hits={len(hits)}")
    for ln in hits[:max_hits]:
        lo=max(1, ln-radius); hi=min(len(txt), ln+radius)
        for j in range(lo, hi+1):
            print(f"{j:4d}: {txt[j-1]}")
        print("---")

show('"principal_2_legs"', radius=18, max_hits=1)
show("def _build_candidates", radius=12, max_hits=1)
show("fallback_value_margin", radius=10, max_hits=2)
