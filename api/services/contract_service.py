from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
import json
import os
from pathlib import Path

# Import robusto: funciona si ejecutas desde repo root o desde /api
try:
    from services.display_enrichment import enrich_contract_inplace, build_display_index
except ModuleNotFoundError:  # ejecución desde repo root
    from api.services.display_enrichment import enrich_contract_inplace, build_display_index  # type: ignore

try:
    from services.picks_classic_multisport import p_safe as classic_p_safe  # type: ignore
except ModuleNotFoundError:  # ejecución desde repo root
    from api.services.picks_classic_multisport import p_safe as classic_p_safe  # type: ignore

CONTRACT_VERSION = "1.0"

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"


# Pisos de cuota para tabs por deporte (UI más atractiva)
PICKS_BY_SPORT_MIN_ODDS = float(os.environ.get("PICKS_BY_SPORT_MIN_ODDS", "1.35"))
PICKS_BY_SPORT_FALLBACK_ODDS = float(os.environ.get("PICKS_BY_SPORT_FALLBACK_ODDS", "1.20"))


def create_empty_contract(contract_date: Optional[str] = None) -> Dict:
    if contract_date is None:
        contract_date = date.today().isoformat()

    return {
        "contract_version": CONTRACT_VERSION,
        "contract_date": contract_date,
        "generated_at": None,
        "picks_classic": [],
        "picks_by_sport": {},  # mapa sport -> lista de picks sin filtros para tabs por deporte
        "picks_parlay_premium": [],
        "daily_featured_parlay": None,
        "metadata": {},
    }


def _load_jsons_from_folder(folder: Path) -> List[Dict]:
    if not folder.exists():
        return []
    items: List[Dict] = []
    for p in sorted(folder.glob("*.json")):
        # Excluir agregadores internos del pipeline (no son picks individuales)
        if p.name in {"parlays.json"}:
            continue
        items.append(json.load(open(p, encoding="utf-8")))
    return items


def _parse_iso_dt(s: object) -> Optional[datetime]:
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


def _cycle_window_utc(day: str) -> Tuple[datetime, datetime]:
    tz = ZoneInfo("Europe/Madrid")
    y, m, d = [int(x) for x in str(day).split("-")]
    start_local = datetime(y, m, d, 6, 0, 0, tzinfo=tz)
    start_utc = start_local.astimezone(ZoneInfo("UTC"))
    end_utc = start_utc + timedelta(hours=24)
    return start_utc, end_utc


def _build_picks_by_sport(day: str) -> Dict[str, List[Dict]]:
    """
    Genera un mapa sport -> picks (top 20 por deporte, sin filtros adicionales) a partir de odds_premium.
    Se usa para las tabs de deportes en la web. Ordenado por seguridad (p_safe).
    """

    odds_path = API_DATA_DIR / "odds_premium" / day / "all.json"
    if not odds_path.exists():
        return {}

    try:
        raw = json.loads(odds_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, list):
        return {}

    display_index = build_display_index(day)
    if display_index:
        start_utc, end_utc = _cycle_window_utc(day)

        def in_window(sport_key: str, eid: str) -> bool:
            disp = display_index.get((sport_key, eid))
            if not isinstance(disp, dict):
                return False
            st = _parse_iso_dt(disp.get("startTime"))
            return bool(st and (st >= start_utc) and (st < end_utc))
    else:
        # Sin snapshots de eventos, aceptamos todo para no vaciar las tabs por deporte.
        def in_window(sport_key: str, eid: str) -> bool:
            return True

    best_by_sport: Dict[str, Dict[Tuple[str, str, str, str], Dict]] = defaultdict(dict)
    fb_by_sport: Dict[str, Dict[Tuple[str, str, str, str], Dict]] = defaultdict(dict)

    def pick_key(p: Dict[str, object]) -> Tuple[str, str, str, str]:
        return (
            str(p.get("sport") or ""),
            str(p.get("eventId") or ""),
            str(p.get("market") or ""),
            str(p.get("selection") or ""),
        )

    for item in raw:
        if not isinstance(item, dict):
            continue

        sport_raw = str(item.get("sport") or "").strip()
        sport = sport_raw.lower()
        eid = str(item.get("eventId") or "").strip()
        if not sport or not eid:
            continue
        if not in_window(sport_raw, eid):
            continue

        try:
            odds = float(item.get("odds") or 0.0)
        except Exception:
            odds = 0.0

        ps = classic_p_safe(item)
        pick = dict(item)
        if ps == ps:  # NaN check
            pick["p_safe"] = round(float(ps), 4)

        key = pick_key(item)

        def _store(target: Dict[str, Dict[Tuple[str, str, str, str], Dict]]):
            existing = target[sport].get(key)
            if existing is None or float(pick.get("p_safe") or -1e9) > float(existing.get("p_safe") or -1e9):
                target[sport][key] = pick

        if odds >= PICKS_BY_SPORT_MIN_ODDS:
            _store(best_by_sport)
        elif odds >= PICKS_BY_SPORT_FALLBACK_ODDS:
            _store(fb_by_sport)

    out: Dict[str, List[Dict]] = {}
    sports_keys = set(best_by_sport.keys()) | set(fb_by_sport.keys())
    for sport in sports_keys:
        picks_map = best_by_sport.get(sport) or {}
        if not picks_map:
            picks_map = fb_by_sport.get(sport) or {}

        picks = list(picks_map.values())
        picks.sort(
            key=lambda p: (
                float(p.get("p_safe") or -1e9),
                float(p.get("odds") or 0.0),
            ),
            reverse=True,
        )
        out[sport] = picks[:20]

    return out


def populate_contract_with_day_data(contract: Dict) -> Dict:
    day = contract["contract_date"]

    # picks_classic: preferimos el agregador all.json (lista plana de picks)
    classic_all = API_DATA_DIR / "picks_classic" / day / "all.json"
    if classic_all.exists():
        contract["picks_classic"] = json.load(open(classic_all, encoding="utf-8"))
    else:
        contract["picks_classic"] = _load_jsons_from_folder(
            API_DATA_DIR / "picks_classic" / day
        )

    # picks_por_deporte: top 20 por sport, sin filtros (para tabs específicas)
    contract["picks_by_sport"] = _build_picks_by_sport(day)

    parlay_dir = API_DATA_DIR / "picks_parlay" / day
    parlays_json = parlay_dir / "parlays.json"

    if parlays_json.exists():
        try:
            loaded = json.load(open(parlays_json, encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("parlays"), list):
                contract["picks_parlay_premium"] = loaded.get("parlays")
            else:
                contract["picks_parlay_premium"] = []
        except Exception:
            contract["picks_parlay_premium"] = []
    else:
        contract["picks_parlay_premium"] = _load_jsons_from_folder(parlay_dir)

    featured_path = API_DATA_DIR / "picks_parlay_featured" / day / "featured_parlay.json"
    if featured_path.exists():
        contract["daily_featured_parlay"] = json.load(open(featured_path, encoding="utf-8"))


    # picks_value: sección opcional (value/inflated singles)
    value_all = API_DATA_DIR / "picks_value" / day / "all.json"
    if value_all.exists():
        contract["picks_value"] = json.load(open(value_all, encoding="utf-8"))
    else:
        contract["picks_value"] = []

    return contract


def freeze_and_save_contract(contract: Dict) -> Dict:
    # ✅ Enriquecimiento determinista con snapshots locales (nombres/logos)
    enrich_contract_inplace(contract)

    now = datetime.utcnow()
    contract["generated_at"] = now.isoformat()
    
    # Freeze 24 horas desde ahora (cuando se procese el último evento)
    freeze_until = now + timedelta(hours=24)
    contract["freeze_until"] = freeze_until.isoformat()

    day = contract["contract_date"]
    base_path = API_DATA_DIR / "contracts" / day
    base_path.mkdir(parents=True, exist_ok=True)

    file_path = base_path / "contract.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(contract, f, ensure_ascii=False, indent=2)

    return contract
