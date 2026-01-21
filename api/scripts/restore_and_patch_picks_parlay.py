from pathlib import Path
import glob, os, time, re
import py_compile

FILE = Path("services/picks_parlay.py")
assert FILE.exists(), f"Missing {FILE}"

# 1) Find newest backup that compiles
baks = sorted(glob.glob("services/picks_parlay.py.bak_*"), key=lambda p: os.path.getmtime(p), reverse=True)
print("BACKUPS_FOUND:", len(baks))

good = None
for b in baks:
    try:
        py_compile.compile(b, doraise=True)
        good = b
        print("FOUND_GOOD_BACKUP:", b)
        break
    except Exception as e:
        pass

if good is None:
    raise SystemExit("No compiling backup found. We must reconstruct manually (paste file).")

# Restore
src = Path(good).read_text(encoding="utf-8")
FILE.write_text(src, encoding="utf-8")
print("RESTORED_FROM:", good)

# Backup restored state
bak2 = FILE.with_suffix(FILE.suffix + f".bak_restore_{int(time.time())}")
bak2.write_text(src, encoding="utf-8")
print("BACKUP_OF_RESTORED:", bak2)

text = src

# 2) Force principal_2_legs guardrails block to be well-formed (indent + keys)
m = re.search(r'("principal_2_legs"\s*:\s*\{\s*\n)(.*?)(\n\s*\}\s*,\s*\n)', text, flags=re.S)
if not m:
    raise RuntimeError("Cannot find principal_2_legs block in PARLAY_GUARDRAILS")

old_body = m.group(2)

def get_val(key, default_literal):
    mm = re.search(rf'^\s*"{re.escape(key)}"\s*:\s*([^,\n]+)', old_body, flags=re.M)
    return mm.group(1).strip() if mm else default_literal

min_leg_probability = get_val("min_leg_probability", "0.62")
max_leg_odds = get_val("max_leg_odds", "2.10")
allowed_market_risk = get_val("allowed_market_risk", '{"low", "medium"}')
min_combined_odds = get_val("min_combined_odds", "1.80")
max_combined_odds = get_val("max_combined_odds", "3.20")
min_leg_edge = get_val("min_leg_edge", "0.0")
min_edge_sum = get_val("min_edge_sum", "0.0")

# Product decision: econ rule + floor + premium margin + fallback margin
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
text = text[:m.start()] + new_block + text[m.end():]

# 3) Patch build_best_parlay to use economic rule and fallback runner (without risky reindent)
lines = text.splitlines(True)

# locate build_best_parlay
i_build = None
for i,l in enumerate(lines):
    if l.startswith("def build_best_parlay"):
        i_build = i
        break
if i_build is None:
    raise RuntimeError("Cannot find def build_best_parlay")

# locate first combo loop
i_loop = None
for i in range(i_build, len(lines)):
    if re.match(r'^\s*for\s+combo\s+in\s+combinations\(', lines[i]):
        i_loop = i
        break
if i_loop is None:
    raise RuntimeError("Cannot find for combo in combinations(...) inside build_best_parlay")

# locate start of sorting block
i_sort = None
for i in range(i_loop, len(lines)):
    if re.search(r'^\s*#\s*Principal:', lines[i]) or re.search(r'^\s*if\s+rule_key\s*==\s*[\'"]principal_2_legs[\'"]\s*:', lines[i]):
        i_sort = i
        break
if i_sort is None:
    raise RuntimeError("Cannot find sorting block to delimit end of combo loop")

loop_block = "".join(lines[i_loop:i_sort])

# Ensure the economic check exists in the loop block; if not, we won't attempt complex surgery here.
if "min_required_prob" not in loop_block:
    raise RuntimeError("Loop block does not contain economic rule yet (min_required_prob missing). Restore earlier state with economic patch first.")

# Ensure fallback not already present
if "fallback_value_margin" not in loop_block:
    # Build fallback loop by cloning and switching margin variable
    fallback_loop = loop_block
    # replace + value_margin with + float(fallback_value_margin) (covers your current code)
    fallback_loop = fallback_loop.replace("+ value_margin", "+ float(fallback_value_margin)")
    # Also handle cases where it was cast already (rare)
    fallback_loop = fallback_loop.replace("+ float(value_margin)", "+ float(fallback_value_margin)")

    insert = (
        "\n"
        "    # Fallback: si premium margin no da candidatos, reintenta con fallback_value_margin\n"
        "    if (not candidates) and (fallback_value_margin is not None) and (float(fallback_value_margin) != float(value_margin)):\n"
        "        candidates = []\n"
        + fallback_loop +
        "\n"
    )

    lines[i_sort:i_sort] = [insert]
    print("INSERTED_FALLBACK_LOOP: yes")
else:
    print("INSERTED_FALLBACK_LOOP: already_present")

text2 = "".join(lines)
FILE.write_text(text2, encoding="utf-8")
print("WROTE_PATCHED:", FILE)

# 4) Final compile check
py_compile.compile(str(FILE), doraise=True)
print("PY_COMPILE_OK:", FILE)

# 5) Show quick proof lines
txt = FILE.read_text(encoding="utf-8").splitlines()
def show(needle, max_hits=5):
    hits = [i for i,l in enumerate(txt, start=1) if needle in l]
    print(f"\nNEEDLE {needle!r} hits={len(hits)}")
    for ln in hits[:max_hits]:
        print(f"{ln:4d}: {txt[ln-1]}")
show("fallback_value_margin")
show("min_required_prob")
show('\"principal_2_legs\"')
