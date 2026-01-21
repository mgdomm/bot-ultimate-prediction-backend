from pathlib import Path
import time
import py_compile

def backup(p: Path, tag: str):
    b = p.with_suffix(p.suffix + f".bak_{tag}_{int(time.time())}")
    b.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    print("BACKUP:", b)

def ensure_import(lines: list[str], import_line: str) -> list[str]:
    if any(import_line.strip() == ln.strip() for ln in lines):
        return lines
    i = 0
    while i < len(lines) and (lines[i].startswith("import ") or lines[i].startswith("from ")):
        i += 1
    lines.insert(i, import_line if import_line.endswith("\n") else import_line + "\n")
    return lines

def patch_main():
    p = Path("api/main.py")
    backup(p, "cycle_day")
    lines = p.read_text(encoding="utf-8").splitlines(True)

    lines = ensure_import(lines, "from api.utils.cycle_day import cycle_day_str\n")

    out = []
    inside_bets = False
    for ln in lines:
        if ln.strip().startswith("def get_today_bets"):
            inside_bets = True

        if inside_bets and "today = date.today().isoformat()" in ln:
            out.append("    today = cycle_day_str()  # 06:00 Europe/Madrid cycle\n")
            continue

        out.append(ln)

        # end function heuristic: next decorator or blank line after return block is fine
        if inside_bets and ln.strip().startswith("return "):
            # do not force end; harmless
            pass

    p.write_text("".join(out), encoding="utf-8")
    print("PATCHED:", p, "(/bets/today uses cycle_day_str)")

def patch_daily_pipeline_if_exists():
    p = Path("api/scripts/daily_pipeline.py")
    if not p.exists():
        print("SKIP:", p, "not found")
        return
    backup(p, "cycle_day")
    lines = p.read_text(encoding="utf-8").splitlines(True)
    lines = ensure_import(lines, "from api.utils.cycle_day import cycle_day_str\n")

    out = []
    for ln in lines:
        # replace ONLY the default fallback
        if "else date.today().isoformat()" in ln:
            out.append(ln.replace("else date.today().isoformat()", "else cycle_day_str()"))
            continue
        out.append(ln)

    p.write_text("".join(out), encoding="utf-8")
    print("PATCHED:", p, "(default day uses cycle_day_str)")

def patch_autoschedule_if_exists():
    p = Path("api/scheduler/autoschedule.py")
    if not p.exists():
        print("SKIP:", p, "not found")
        return
    backup(p, "cycle_day")
    lines = p.read_text(encoding="utf-8").splitlines(True)
    lines = ensure_import(lines, "from api.utils.cycle_day import cycle_day_str\n")

    out = []
    for ln in lines:
        if "day = date.today().isoformat()" in ln:
            out.append("    day = cycle_day_str()  # 06:00 Europe/Madrid cycle\n")
            continue
        out.append(ln)

    p.write_text("".join(out), encoding="utf-8")
    print("PATCHED:", p, "(scheduler job uses cycle_day_str for lock/day)")

def main():
    patch_main()
    patch_daily_pipeline_if_exists()
    patch_autoschedule_if_exists()

    # compile checks
    py_compile.compile("api/utils/cycle_day.py", doraise=True)
    py_compile.compile("api/main.py", doraise=True)
    if Path("api/scheduler/autoschedule.py").exists():
        py_compile.compile("api/scheduler/autoschedule.py", doraise=True)
    if Path("api/scripts/daily_pipeline.py").exists():
        py_compile.compile("api/scripts/daily_pipeline.py", doraise=True)

    print("PY_COMPILE_OK")

if __name__ == "__main__":
    main()
