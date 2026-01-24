from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
import json
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
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))

    # DF_ENRICH_CONTRACT_ON_READ: enriquecer en memoria (no re-escribe el contrato en disco)
    try:
        enrich_contract_inplace(contract)
    except Exception as err:
        print('[display_enrichment] failed:', err)

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


# ✅ Operational healthcheck (no business logic)
@app.get("/health")
def health_check():
    return {"status": "ok"}
