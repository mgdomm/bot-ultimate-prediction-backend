from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import json
import os
import sys
import subprocess
import time
import html
import urllib.request
import urllib.parse
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

# ---------------------------------------------------------------------------
# Flashscore (Livesport) lightweight resolver (READ-ONLY; in-memory cache only)
# ---------------------------------------------------------------------------

_FLASH_TEAM_CACHE = {}   # (sport_name, norm_team_name) -> {"exp": float, "value": {...}}
_FLASH_MATCH_CACHE = {}  # (sport_path, home_norm, away_norm, expected_date) -> {"exp": float, "value": {...}}

def _flash_now() -> float:
    return time.time()

def _flash_norm_name(s: object) -> str:
    t = (str(s) if s is not None else "").strip().lower()
    # stable, dependency-free normalization
    out = []
    for ch in t:
        if ch.isalnum():
            out.append(ch)
        else:
            out.append(" ")
    return " ".join("".join(out).split())

def _flash_http_get_json(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ultimate-predictor/1.0 (flashscore-resolver; +https://example.invalid)",
            "Accept": "application/json,text/plain,*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read().decode("utf-8", "replace")
    return json.loads(raw)

def _flash_http_get_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ultimate-predictor/1.0 (flashscore-resolver; +https://example.invalid)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", "replace")

def _flash_pick_date_from_title_html(html_text: str):
    """Extract dd/mm/yyyy from <title>... without regex (best-effort)."""
    lo = html_text.lower()
    a = lo.find("<title>")
    if a < 0:
        return None
    b = lo.find("</title>", a)
    if b < 0:
        return None
    title = html.unescape(html_text[a + len("<title>"):b]).strip()
    for i in range(0, max(0, len(title) - 10)):
        chunk = title[i:i+10]
        if (
            len(chunk) == 10
            and chunk[0:2].isdigit()
            and chunk[2] == "/"
            and chunk[3:5].isdigit()
            and chunk[5] == "/"
            and chunk[6:10].isdigit()
        ):
            return chunk
    return None

def _flash_sport_map(sport: str):
    """Return (sport_path_for_flashscore_url, sport_name_for_livesport_filter)."""
    s = (sport or "").strip().lower()
    mapping = {
        "football": ("football", "Soccer"),
        "soccer": ("football", "Soccer"),
        "basketball": ("basketball", "Basketball"),
        "tennis": ("tennis", "Tennis"),
        "hockey": ("hockey", "Hockey"),
        "icehockey": ("hockey", "Hockey"),
        "handball": ("handball", "Handball"),
        "rugby": ("rugby", "Rugby"),
        "volleyball": ("volleyball", "Volleyball"),
        "baseball": ("baseball", "Baseball"),
        "american-football": ("american-football", "American football"),
    }
    if s in mapping:
        return mapping[s]
    return (s or "football"), ""

def _flash_resolve_team(sport_name: str, team_name: str):
    norm = _flash_norm_name(team_name)
    if not norm:
        return None

    ck = (sport_name or "", norm)
    hit = _FLASH_TEAM_CACHE.get(ck)
    if isinstance(hit, dict) and hit.get("exp", 0) > _flash_now():
        return hit.get("value")

    q = urllib.parse.quote_plus(team_name.strip())
    data = _flash_http_get_json(f"https://s.livesport.services/api/v2/search/?q={q}")
    if not isinstance(data, list):
        return None

    candidates = []
    for it in data:
        if not isinstance(it, dict):
            continue
        tname = (it.get("type") or {}).get("name") if isinstance(it.get("type"), dict) else None
        if tname != "Team":
            continue
        sname = (it.get("sport") or {}).get("name") if isinstance(it.get("sport"), dict) else None
        if sport_name and sname != sport_name:
            continue
        candidates.append(it)

    if not candidates:
        return None

    chosen = None
    for it in candidates:
        if _flash_norm_name(it.get("name")) == norm:
            chosen = it
            break
    if chosen is None:
        chosen = candidates[0]

    value = {
        "name": chosen.get("name") or team_name,
        "id": chosen.get("id"),
        "slug": chosen.get("url"),
    }

    _FLASH_TEAM_CACHE[ck] = {"exp": _flash_now() + 7 * 24 * 3600, "value": value}
    return value


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

        # If a frozen contract exists but is empty (can happen after deploy/ephemeral FS),
        # rebuild in-memory from local pick artifacts (NO external API calls; NO disk writes).
        try:
            def _has_any_picks(c: dict) -> bool:
                if not isinstance(c, dict):
                    return False
                pc = c.get("picks_classic") or []
                pp = c.get("picks_parlay_premium") or []
                pv = c.get("picks_value") or []
                return (isinstance(pc, list) and len(pc) > 0) or (isinstance(pp, list) and len(pp) > 0) or (isinstance(pv, list) and len(pv) > 0)

            if not _has_any_picks(contract):
                rebuilt = create_empty_contract(today)
                rebuilt = populate_contract_with_day_data(rebuilt)
                # preserve generated_at if it existed (useful for debugging)
                if contract.get("generated_at") and not rebuilt.get("generated_at"):
                    rebuilt["generated_at"] = contract.get("generated_at")
                md = rebuilt.get("metadata")
                if not isinstance(md, dict):
                    md = {}
                    rebuilt["metadata"] = md
                md["rebuilt_from_local_picks"] = True
                contract = rebuilt
        except Exception as err:
            print('[contract_rebuild] failed:', err)

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




# ---------------------------------------------------------------------------
# Flashscore match URL resolver (READ-ONLY)
# ---------------------------------------------------------------------------
@app.get("/flashscore/match_url")
def flashscore_match_url(
    sport: str = "football",
    home: str = "",
    away: str = "",
    start: str = "",
):
    """Resolve a Flashscore match URL by resolving home/away teams via Livesport search.
    READ-ONLY (no disk writes). Does NOT call /internal/ensure_today.
    """
    home = (home or "").strip()
    away = (away or "").strip()
    if not home or not away:
        raise HTTPException(status_code=400, detail="home and away are required")

    sport_path, sport_name = _flash_sport_map(sport)

    expected_date = None
    dt = _parse_iso_dt(start)
    if dt is not None:
        local = dt.astimezone(ZoneInfo("Europe/Madrid"))
        expected_date = f"{local.day:02d}/{local.month:02d}/{local.year:04d}"

    home_norm = _flash_norm_name(home)
    away_norm = _flash_norm_name(away)

    mk = (sport_path, home_norm, away_norm, expected_date or "")
    mhit = _FLASH_MATCH_CACHE.get(mk)
    if isinstance(mhit, dict) and mhit.get("exp", 0) > _flash_now():
        return mhit.get("value")

    home_team = _flash_resolve_team(sport_name, home)
    away_team = _flash_resolve_team(sport_name, away)

    if (
        not home_team or not away_team
        or not home_team.get("id") or not away_team.get("id")
        or not home_team.get("slug") or not away_team.get("slug")
    ):
        out = {
            "match_url": None,
            "verified": False,
            "sport": sport_path,
            "home": home_team or {"name": home},
            "away": away_team or {"name": away},
            "expected_date": expected_date,
        }
        _FLASH_MATCH_CACHE[mk] = {"exp": _flash_now() + 15 * 60, "value": out}
        return out

    match_url = (
        f"https://www.flashscore.com/match/{sport_path}/"
        f"{home_team['slug']}-{home_team['id']}/"
        f"{away_team['slug']}-{away_team['id']}/"
        f"?isDetailPopup=true"
    )

    verified = False
    if expected_date:
        try:
            page = _flash_http_get_text(match_url)
            got = _flash_pick_date_from_title_html(page)
            verified = (got == expected_date)
        except Exception:
            verified = False

    out = {
        "match_url": match_url,
        "verified": verified,
        "sport": sport_path,
        "home": {"name": home_team.get("name"), "id": home_team.get("id"), "slug": home_team.get("slug")},
        "away": {"name": away_team.get("name"), "id": away_team.get("id"), "slug": away_team.get("slug")},
        "expected_date": expected_date,
    }
    _FLASH_MATCH_CACHE[mk] = {"exp": _flash_now() + 6 * 3600, "value": out}
    return out



# ---------------------------------------------------------------------------
# Live events snapshot (API-SPORTS) — READ-ONLY (in-memory cache)
# ---------------------------------------------------------------------------

_LIVE_EVENTS_CACHE = {}  # (sport, ids_csv) -> {"exp": float, "value": dict}

def _api_sports_http_get_json(url: str) -> dict:
    api_key = os.environ.get("API_SPORTS_KEY") or ""
    if not api_key:
        # Keep read-only behavior: return empty instead of 500 so UI can fallback.
        return {"results": 0, "response": [], "errors": {"message": "API_SPORTS_KEY missing"}}

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ultimate-predictor/1.0 (live-snapshot)",
            "Accept": "application/json",
            "x-apisports-key": api_key,
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode("utf-8", "replace")
    data = json.loads(raw)
    # API-SPORTS sometimes returns {"errors":{...}} with 200
    if isinstance(data, dict) and data.get("errors"):
        # Do not raise: keep it 200 so frontend can fallback without breaking.
        return data
    if not isinstance(data, dict):
        return {"results": 0, "response": [], "errors": {"message": "invalid json"}}
    return data

def _live_endpoint_for_sport(sport: str) -> str:
    s = (sport or "").strip().lower()
    # align with events_ingestion.py
    if s in ("football", "soccer"):
        return "/fixtures"
    # most API-Sports products use /games
    return "/games"

def _live_base_url_for_sport(sport: str) -> str:
    try:
        from api.services.api_sports_hosts import SPORT_BASE_URL as _SB  # type: ignore
    except ModuleNotFoundError:
        from services.api_sports_hosts import SPORT_BASE_URL as _SB  # type: ignore
    base = _SB.get((sport or "").strip().lower())
    if not base:
        return ""
    return str(base).rstrip("/")

def _extract_live_for_item(sport: str, item: dict) -> tuple[str | None, dict | None]:
    s = (sport or "").strip().lower()

    # football /fixtures response shape
    if s in ("football", "soccer"):
        fixture = item.get("fixture") if isinstance(item.get("fixture"), dict) else {}
        eid = fixture.get("id")
        if eid is None:
            return None, None
        status = fixture.get("status") if isinstance(fixture.get("status"), dict) else {}
        goals = item.get("goals") if isinstance(item.get("goals"), dict) else {}
        live = {
            "statusLong": status.get("long"),
            "statusShort": status.get("short"),
            "elapsed": status.get("elapsed"),
            "extra": status.get("extra"),
            "homeScore": goals.get("home"),
            "awayScore": goals.get("away"),
        }
        return str(eid), live

    # generic /games shape (handball/hockey/basketball/rugby/volleyball/baseball/afl/nba)
    eid = item.get("id")
    if eid is None and isinstance(item.get("game"), dict):
        eid = item["game"].get("id")  # nfl/american-football sometimes nests this way
    if eid is None:
        return None, None

    status = item.get("status") if isinstance(item.get("status"), dict) else {}
    scores = item.get("scores") if isinstance(item.get("scores"), dict) else {}
    home_scores = scores.get("home")
    away_scores = scores.get("away")
    home_total = home_scores.get("total") if isinstance(home_scores, dict) else home_scores
    away_total = away_scores.get("total") if isinstance(away_scores, dict) else away_scores

    live = {
        "statusLong": status.get("long"),
        "statusShort": status.get("short"),
        "timer": status.get("timer") or item.get("timer"),
        "time": item.get("time"),
        "homeScore": home_total,
        "awayScore": away_total,
        "periods": item.get("periods"),
    }
    return str(eid), live

def _ids_list_from_csv(ids_csv: str) -> list[str]:
    return [x.strip() for x in str(ids_csv or "").split(",") if x.strip()]

def _ids_set_from_csv(ids_csv: str) -> set[str]:
    return set(_ids_list_from_csv(ids_csv))

@app.get("/live/events")
def live_events(sport: str = "", ids: str = ""):
    """
    Fetch live status for specific events via API-SPORTS.
    READ-ONLY: no contract writes, no pipeline, cache in-memory.
    Returns 200 even on upstream issues (empty map) so UI can fallback.
    """
    sport = (sport or "").strip().lower()
    ids_csv = ",".join([x.strip() for x in str(ids or "").split(",") if x.strip()])
    if not sport or not ids_csv:
        raise HTTPException(status_code=400, detail="sport and ids are required")

    ck = (sport, ids_csv)
    now = time.time()
    hit = _LIVE_EVENTS_CACHE.get(ck)
    if isinstance(hit, dict) and hit.get("exp", 0) > now:
        return hit.get("value")

    base = _live_base_url_for_sport(sport)
    if not base:
        out = {"sport": sport, "ids": ids_csv, "live_by_id": {}, "errors": {"message": "sport not supported"}}
        _LIVE_EVENTS_CACHE[ck] = {"exp": now + 60, "value": out}
        return out

    endpoint = _live_endpoint_for_sport(sport)
    wanted = _ids_set_from_csv(ids_csv)
    ids_list = _ids_list_from_csv(ids_csv)
    single_id = ids_list[0] if len(ids_list) == 1 else ""

    # API-Sports Free plan may block `ids` (plural). Strategy:
    # - if single id: use `id`
    # - if multiple: use `live=all` (1 request) then filter by ids
    params = {"id": single_id} if single_id else {"live": "all"}
    url = base + endpoint + "?" + urllib.parse.urlencode(params)

    data = _api_sports_http_get_json(url)
    resp = data.get("response") if isinstance(data, dict) else None
    out_map = {}
    if isinstance(resp, list):
        for it in resp:
            if not isinstance(it, dict):
                continue
            eid, live = _extract_live_for_item(sport, it)
            if eid and isinstance(live, dict) and eid in wanted:
                out_map[eid] = live

    out = {
        "sport": sport,
        "ids": ids_csv,
        "live_by_id": out_map,
        "upstream_errors": data.get("errors") if isinstance(data, dict) else None,
        "fetched_at": datetime.utcnow().isoformat(),
    }

    # TTL: short, to protect quota across many users
    _LIVE_EVENTS_CACHE[ck] = {"exp": now + 90, "value": out}
    return out

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
