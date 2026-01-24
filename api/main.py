from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import json
import os
import sys
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

# Make imports work both ways:
# - uvicorn api.main:app (repo root)
# - uvicorn main:app (rootDir=api)
try:
    from api.scheduler.autoschedule import init_scheduler
    from api.utils.cycle_day import cycle_day_str
except ModuleNotFoundError:
    from scheduler.autoschedule import init_scheduler
    from utils.cycle_day import cycle_day_str



# Display enrichment (attach logos + live scores from local event snapshots)
try:
    from api.services.display_enrichment import enrich_contract_inplace, build_display_index
except ModuleNotFoundError:
    from services.display_enrichment import enrich_contract_inplace, build_display_index  # type: ignore


# Contract building (fallback when contract.json is missing)
try:
    from api.services.contract_service import create_empty_contract, populate_contract_with_day_data
except ModuleNotFoundError:
    from services.contract_service import create_empty_contract, populate_contract_with_day_data  # type: ignore

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[1]
API_DATA_DIR = REPO_ROOT / "api" / "data"

def _parse_iso_dt(s: object):
    if not s:
        return None
    try:
        t = str(s)
        if t.endswith("Z"):
            t = t[:-1] + "+00:00"
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return dt
    except Exception:
        return None

def _cycle_window_local(day: str):
    # 06:00 Europe/Madrid -> 06:00 next day (end exclusivo)
    tz = ZoneInfo("Europe/Madrid")
    y, m, d = [int(x) for x in day.split("-")]
    start = datetime(y, m, d, 6, 0, 0, tzinfo=tz)
    end = start + timedelta(hours=24)
    return start, end

def _pick_in_window(pick: dict, start_local: datetime, end_local: datetime) -> bool:
    disp = pick.get("display")
    if not isinstance(disp, dict):
        return False
    st = _parse_iso_dt(disp.get("startTime"))
    if st is None:
        return False
    st_local = st.astimezone(start_local.tzinfo)  # Europe/Madrid
    return (st_local >= start_local) and (st_local < end_local)

def _filter_contract_to_cycle_window_inplace(contract: dict) -> bool:
    day = contract.get("contract_date") or contract.get("cycle_day") or contract.get("day")
    if not day:
        return False

    start_local, end_local = _cycle_window_local(str(day))

    changed = False

    # Classic
    pc = contract.get("picks_classic") or []
    new_pc = []
    if isinstance(pc, list):
        for item in pc:
            if isinstance(item, dict):
                if _pick_in_window(item, start_local, end_local):
                    new_pc.append(item)
                else:
                    changed = True
            elif isinstance(item, list):
                # soportar estructura antigua list-of-lists
                for pick in item:
                    if isinstance(pick, dict):
                        if _pick_in_window(pick, start_local, end_local):
                            new_pc.append(pick)
                        else:
                            changed = True
            else:
                changed = True
    contract["picks_classic"] = new_pc

    # Parlay premium: descartar parleys con legs fuera de ventana
    pp = contract.get("picks_parlay_premium") or []
    if isinstance(pp, list):
        new_pp = []
        for par in pp:
            if not isinstance(par, dict):
                changed = True
                continue
            legs = par.get("legs")
            if not isinstance(legs, list):
                legs = par.get("picks")
            if not isinstance(legs, list) or len(legs) == 0:
                changed = True
                continue
            ok = True
            for leg in legs:
                if not isinstance(leg, dict) or (not _pick_in_window(leg, start_local, end_local)):
                    ok = False
                    break
            if ok:
                new_pp.append(par)
            else:
                changed = True
        contract["picks_parlay_premium"] = new_pp

    # Featured parlay: si está fuera, lo quitamos
    feat = contract.get("daily_featured_parlay")
    if isinstance(feat, dict):
        legs = feat.get("legs")
        if not isinstance(legs, list):
            legs = feat.get("picks")
        ok = True
        if not isinstance(legs, list) or len(legs) == 0:
            ok = False
        else:
            for leg in legs:
                if not isinstance(leg, dict) or (not _pick_in_window(leg, start_local, end_local)):
                    ok = False
                    break
        if not ok:
            contract["daily_featured_parlay"] = None
            changed = True

    # metadata
    md = contract.get("metadata")
    if not isinstance(md, dict):
        md = {}
        contract["metadata"] = md
        changed = True
    md["cycle_window"] = {"tz": "Europe/Madrid", "start": start_local.isoformat(), "end_exclusive": end_local.isoformat()}

    return changed


# DF_DIAG_MAIN_LIVE_SNAPSHOTS
_DF_DIAG_LIVE_DONE_DAYS = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # from api.scheduler.daily_lock import run_daily_lock  # disabled
        # run_daily_lock()  # disabled: daily_pipeline runs at 06:00
        print("[LOCK] Daily contract ensured")
    except Exception as e:
        print(f"[LOCK] Failed to build daily contract: {e}")
    yield


app = FastAPI(

    title="Bot Ultimate Prediction API",
    lifespan=lifespan,
)

# Internal daily scheduler (06:00 Europe/Madrid)
init_scheduler(app)

# ✅ CORS (necesario para llamadas desde el navegador: Next dev server en :3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bot-ultimate-prediction-web.onrender.com",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Global response headers (API versioning & semantic freeze)
@app.middleware("http")
async def add_api_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "1"
    response.headers["X-Contract-Centric"] = "true"
    response.headers["X-API-Frozen"] = "true"
    response.headers["Cache-Control"] = "no-store"
    return response


# ✅ READ-ONLY endpoint (contrato = única verdad)
# ✅ READ-ONLY endpoint (contrato = única verdad)
@app.get("/bets/today")
def get_today_bets():
    today = cycle_day_str()  # 06:00 Europe/Madrid cycle
    contract_path = API_DATA_DIR / "contracts" / today / "contract.json"

    if not contract_path.exists():
        # Fallback confiable: construir contrato desde snapshots locales (sin llamar APIs externas)
        contract = create_empty_contract(today)
        contract = populate_contract_with_day_data(contract)
        if not contract.get("generated_at"):
            contract["generated_at"] = datetime.utcnow().isoformat()
        try:
            enrich_contract_inplace(contract)
        except Exception as err:
            print('[display_enrichment] failed:', err)
        # NOTE: Do NOT persist fallback contracts from /bets/today.
        # The daily pipeline is the only writer of api/data/contracts/<day>/contract.json.
    else:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))

    # DF_ENRICH_CONTRACT_ON_READ: enriquecer en memoria (no re-escribe el contrato en disco)
    try:
        enrich_contract_inplace(contract)
    except Exception as err:
        print('[display_enrichment] failed:', err)

    # DF_CYCLE_WINDOW_FILTER: asegurar ventana 06:00->06:00 Europe/Madrid (evita partidos viejos)
    try:
        changed = _filter_contract_to_cycle_window_inplace(contract)
        if changed:
            # NOTE: Do NOT rewrite the frozen contract on read.
            # Filter in-memory only; otherwise transient enrichment/window issues can permanently drop picks/parlays.
            pass
    except Exception as err:
        print('[cycle_window_filter] failed:', err)

    # DF_DIAG_MAIN_LIVE_SNAPSHOTS: log solo si hay picks pero 0 live (1 vez por día/proceso)
    try:
        total = 0
        with_live = 0
        def _iter_picks(c):
            pc = c.get('picks_classic') or []
            for container in pc:
                if isinstance(container, list):
                    for pick in container:
                        if isinstance(pick, dict):
                            yield pick
                elif isinstance(container, dict):
                    yield container
            pp = c.get('picks_parlay_premium') or []
            if isinstance(pp, list):
                for par in pp:
                    if not isinstance(par, dict):
                        continue
                    legs = par.get('legs')
                    if not isinstance(legs, list):
                        legs = par.get('picks')
                    if isinstance(legs, list):
                        for leg in legs:
                            if isinstance(leg, dict):
                                yield leg
            feat = c.get('daily_featured_parlay')
            if isinstance(feat, dict):
                legs = feat.get('legs')
                if not isinstance(legs, list):
                    legs = feat.get('picks')
                if isinstance(legs, list):
                    for leg in legs:
                        if isinstance(leg, dict):
                            yield leg
        for pick in _iter_picks(contract):
            total += 1
            disp = pick.get('display')
            if isinstance(disp, dict) and disp.get('live') is not None:
                with_live += 1
        if total > 0 and with_live == 0 and today not in _DF_DIAG_LIVE_DONE_DAYS:
            _DF_DIAG_LIVE_DONE_DAYS.add(today)
            idx = build_display_index(today)  # solo lee api/data/events/<day>/*.json
            idx_total = len(idx)
            idx_live = 0
            by_sport = {}
            for (sport, _eid), d in idx.items():
                if isinstance(d, dict) and d.get('live') is not None:
                    idx_live += 1
                    s = str(sport)
                    by_sport[s] = by_sport.get(s, 0) + 1
            print(json.dumps({
                'diag': 'DF_DIAG_MAIN_LIVE_SNAPSHOTS',
                'day': today,
                'picks_total': total,
                'picks_with_live': with_live,
                'snapshot_index_total': idx_total,
                'snapshot_index_with_live': idx_live,
                'snapshot_index_with_live_by_sport': by_sport,
            }, ensure_ascii=False), flush=True)
    except Exception as err:
        print(json.dumps({
            'diag': 'DF_DIAG_MAIN_LIVE_SNAPSHOTS_ERROR',
            'error': str(err),
        }, ensure_ascii=False), flush=True)

    # Expose cycle day explicitly (client-friendly; does not change frozen contract on disk)
    contract['cycle_day'] = today
    contract['day'] = today


    # Backwards-compatible aliases for clients that expect `parlays`
    # Prefer aggregator {"parlays":[...]} if present (avoids duplicates)
    premium = contract.get("picks_parlay_premium", [])
    parlays = []

    if isinstance(premium, list):
        agg = None
        for item in premium:
            if isinstance(item, dict) and isinstance(item.get("parlays"), list) and len(item["parlays"]) > 0:
                agg = item["parlays"]
                break
        if agg is not None:
            parlays = agg
        else:
            for item in premium:
                if isinstance(item, dict) and "legs" in item:
                    parlays.append(item)

    contract["parlays"] = parlays

    # Backwards-compatible alias for clients that expect `classic`
    contract["classic"] = contract.get("picks_classic", [])

    # Optional alias: value singles
    contract["value"] = contract.get("picks_value", [])

    # featured alias (optional)
    if contract.get("daily_featured_parlay") is not None:
        contract["featured_parlay"] = contract["daily_featured_parlay"]

    return contract



# ✅ Internal trigger: ensure today's contract exists (for external cron; avoids Render sleep issues)
# Set env INTERNAL_ENSURE_TOKEN and call:
#   GET /internal/ensure_today?token=...
@app.get("/internal/ensure_today")
def internal_ensure_today(token: str = ""):
    expected = os.environ.get("INTERNAL_ENSURE_TOKEN") or ""
    if not expected or token != expected:
        raise HTTPException(status_code=404, detail="Not found")

    day = cycle_day_str()  # 06:00 Europe/Madrid cycle
    contract_path = API_DATA_DIR / "contracts" / day / "contract.json"
    lock_file = f"/tmp/internal_ensure_lock_{day}"

    def _contract_is_complete() -> bool:
        """True only when the frozen contract has the minimum expected sections.

        /bets/today can create a fallback contract (e.g. classic-only) when the
        instance was asleep and the pipeline didn't run. Treat that as incomplete
        so external cron can force the pipeline.
        """
        if not contract_path.exists():
            return False
        try:
            c = json.loads(contract_path.read_text(encoding="utf-8"))
        except Exception:
            return False
        if not isinstance(c, dict):
            return False

        pc = c.get("picks_classic") or []
        pp = c.get("picks_parlay_premium") or []
        dfp = c.get("daily_featured_parlay")

        classic_ok = isinstance(pc, list) and len(pc) > 0
        parlay_ok = (isinstance(pp, list) and len(pp) > 0) or isinstance(dfp, dict)

        return classic_ok and parlay_ok

    if _contract_is_complete():
        return {"ok": True, "day": day, "ran_pipeline": False, "reason": "contract_already_complete"}

    if os.path.exists(lock_file):
        return {"ok": True, "day": day, "ran_pipeline": False, "reason": "lock_exists"}

    try:
        with open(lock_file, "w", encoding="utf-8") as f:
            f.write("locked")

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT)
        cmd = [sys.executable, "-u", str(REPO_ROOT / "api" / "scripts" / "daily_pipeline.py"), day]
        subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, check=True)

        return {"ok": True, "day": day, "ran_pipeline": True, "reason": "pipeline_executed"}
    finally:
        try:
            if os.path.exists(lock_file):
                os.unlink(lock_file)
        except Exception:
            pass

# ✅ Operational healthcheck (no business logic)
@app.get("/health")
def health_check():
    return {"status": "ok"}
