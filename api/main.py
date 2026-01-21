from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
import json
from contextlib import asynccontextmanager
from pathlib import Path
from api.scheduler.autoschedule import init_scheduler
from api.utils.cycle_day import cycle_day_str


# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[1]
API_DATA_DIR = REPO_ROOT / "api" / "data"


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
        raise HTTPException(status_code=404, detail="Daily contract not found")

    contract = json.loads(contract_path.read_text(encoding="utf-8"))

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
