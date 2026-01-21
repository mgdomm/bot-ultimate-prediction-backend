import os, sys, subprocess, json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional

from api.utils.cycle_day import cycle_day_str
from api.utils.paths import data_path, ensure_dir

REPO = Path(__file__).resolve().parents[2]

def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def run(cmd, env):
    print(f"[{ts()}] RUN: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(REPO), env=env, check=True)

def dir_has_nonempty_json(dirpath: Path) -> bool:
    if not dirpath.exists() or not dirpath.is_dir():
        return False
    for p in sorted(dirpath.glob("*.json")):
        try:
            if p.stat().st_size > 2:  # > "[]"
                return True
        except Exception:
            pass
    return False

def file_nonempty(p: Path) -> bool:
    return p.exists() and p.is_file() and p.stat().st_size > 2

def json_file_has_nonempty_list_key(p: Path, key: str) -> bool:
    if not file_nonempty(p):
        return False
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        v = obj.get(key) if isinstance(obj, dict) else None
        return isinstance(v, list) and len(v) > 0
    except Exception:
        return False

def odds_file_has_data(p: Path) -> bool:
    """
    Considera NO válido:
      - missing
      - []
      - {}
      - dict con response=[] (típico api-sports sin resultados)
    """
    if not p.exists() or not p.is_file():
        return False
    if p.stat().st_size <= 2:
        return False
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return False

    if obj == [] or obj == {}:
        return False

    if isinstance(obj, dict):
        resp = obj.get("response")
        if isinstance(resp, list):
            return len(resp) > 0
        # si no hay response, al menos que tenga contenido
        return len(obj.keys()) > 0

    if isinstance(obj, list):
        return len(obj) > 0

    return True

def main():
    args = [a for a in sys.argv[1:] if a.strip()]
    force = "--force" in args
    args = [a for a in args if a != "--force"]

    day = args[0] if args else cycle_day_str()
    print(f"[{ts()}] DAILY_PIPELINE cycle_day={day} force={force}")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO)

    # outputs (verdad única)
    events_dir      = data_path("events", day)
    odds_dir        = data_path("odds", day)
    odds_norm       = data_path("odds_normalized", day, "all.json")
    odds_prob       = data_path("odds_probability", day, "all.json")
    odds_est        = data_path("odds_estimated", day, "all.json")
    odds_ev         = data_path("odds_ev", day, "all.json")
    odds_risk       = data_path("odds_risk", day, "all.json")
    odds_premium    = data_path("odds_premium", day, "all.json")
    parlay_eligible = data_path("pools", day, "parlay_eligible.json")
    picks_parlay    = data_path("picks_parlay", day, "parlays.json")
    picks_classic_d = data_path("picks_classic", day)
    contract_path   = data_path("contracts", day, "contract.json")

    # 0) events
    if dir_has_nonempty_json(events_dir) and not force:
        print(f"[{ts()}] SKIP events_ingestion (exists): {events_dir}")
    else:
        ensure_dir(events_dir)
        print(f"[{ts()}] DO   events_ingestion -> {events_dir}")
        run([sys.executable, "-u", "api/services/events_ingestion.py", day], env)

    # 1) odds ingestion (solo deportes vacíos; evita gastar API de más)
    from api.services.odds_ingestion_multisport import ODDS_MODE_BY_SPORT  # import local (sin requests)

    need_sports: List[str] = []
    for sport in sorted(ODDS_MODE_BY_SPORT.keys()):
        p = odds_dir / f"{sport}.json"
        if force or (not odds_file_has_data(p)):
            need_sports.append(sport)

    ran_odds_ingest = False
    if len(need_sports) == 0:
        print(f"[{ts()}] SKIP odds_ingestion_multisport (all sports have data): {odds_dir}")
    else:
        ensure_dir(odds_dir)
        max_events = os.environ.get("ODDS_MAX_EVENTS_PER_SPORT", "40")
        cmd = [sys.executable, "-u", "api/services/odds_ingestion_multisport.py", day, "--sports", ",".join(need_sports), "--max-events", str(max_events)]
        if force:
            cmd.append("--force")
        print(f"[{ts()}] DO   odds_ingestion_multisport sports={need_sports} max_events={max_events} -> {odds_dir}")
        run(cmd, env)
        ran_odds_ingest = True

    # If odds changed, recompute everything downstream (even if files exist)
    recompute_downstream = force or ran_odds_ingest

    chain = [
        ("odds_normalization_multisport", odds_norm, [sys.executable, "-u", "api/services/odds_normalization_multisport.py", day]),
        ("odds_probability_multisport",   odds_prob, [sys.executable, "-u", "api/services/odds_probability_multisport.py", day]),
        ("odds_estimation_multisport",    odds_est,  [sys.executable, "-u", "api/services/odds_estimation_multisport.py", day]),
        ("odds_ev_multisport",            odds_ev,   [sys.executable, "-u", "api/services/odds_ev_multisport.py", day]),
        ("odds_risk_multisport",          odds_risk, [sys.executable, "-u", "api/services/odds_risk_multisport.py", day]),
        ("odds_premium_multisport",       odds_premium, [sys.executable, "-u", "api/services/odds_premium_multisport.py", day]),
        ("inflated_pool_builder",         parlay_eligible, [sys.executable, "-u", "api/services/inflated_pool_builder.py", day]),
        ("picks_parlay_premium_multisport", picks_parlay, [sys.executable, "-u", "api/services/picks_parlay_premium_multisport.py", day]),
        ("picks_classic_multisport",      picks_classic_d, [sys.executable, "-u", "api/services/picks_classic_multisport.py", day]),
    ]

    for name, out, cmd in chain:
        # custom "ok" checks
        if out.is_dir():
            ok = dir_has_nonempty_json(out)
        else:
            if name == "picks_parlay_premium_multisport":
                ok = json_file_has_nonempty_list_key(out, "parlays")  # FIX: no basta con "exists"
            else:
                ok = file_nonempty(out) if out.suffix == ".json" else out.exists()

        if ok and (not recompute_downstream):
            print(f"[{ts()}] SKIP {name} (exists): {out}")
            continue

        ensure_dir(out if out.is_dir() else out.parent)
        print(f"[{ts()}] DO   {name} -> {out}")
        run(cmd, env)

        # once we run any downstream step, keep recomputing the rest
        recompute_downstream = True

    # freeze contract
    print(f"[{ts()}] FREEZE contract from local picks for cycle_day={day}")
    from api.services.contract_service import create_empty_contract, populate_contract_with_day_data, freeze_and_save_contract
    c = create_empty_contract(day)
    c = populate_contract_with_day_data(c)
    c = freeze_and_save_contract(c)

    print(f"[{ts()}] DONE contract={contract_path} exists={contract_path.exists()} size={(contract_path.stat().st_size if contract_path.exists() else None)}")
    print(f"[{ts()}] QUICK CHECK:")
    print(" events_dir:", events_dir, "nonempty_json:", dir_has_nonempty_json(events_dir))
    print(" odds_dir:", odds_dir, "nonempty_json:", dir_has_nonempty_json(odds_dir))
    for p in [odds_norm, odds_ev, odds_risk, odds_premium, parlay_eligible, picks_parlay, contract_path]:
        print(" -", p, "exists=", p.exists(), "size=", (p.stat().st_size if p.exists() else None))

if __name__ == "__main__":
    main()
