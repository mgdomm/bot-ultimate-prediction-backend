"""
Internal scheduler (Render-friendly)

- Runs inside the *same* web service process (so generated files are visible to /bets/today).
- Avoids re-running if today's contract already has picks.
- Uses /tmp lock to avoid concurrent runs.
- Executes the full pipeline: api/scripts/daily_pipeline.py <cycle_day>
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def _robust_import(module_name: str):
    """Importa modulo con multiples estrategias"""
    try:
        __import__(f"api.{module_name}", fromlist=[""])
        return sys.modules[f"api.{module_name}"]
    except ImportError:
        pass

    root_path = Path(__file__).parent.parent
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

    try:
        __import__(module_name, fromlist=[""])
        return sys.modules[module_name]
    except ImportError as e:
        logger.error(f"Fallback import fallo {module_name}: {e}")
        raise

cycle_day_mod = _robust_import("utils.cycle_day")
cycle_day_str = cycle_day_mod.cycle_day_str

# Repo root: .../bot-ultimate-prediction
REPO_ROOT = Path(__file__).resolve().parents[2]
API_DATA_DIR = REPO_ROOT / "api" / "data"

# DF_BACKOFF_V1
# Backoff simple para evitar reintentos frecuentes cuando la API falla (ej. cuenta suspendida).
# Persistimos estado en /tmp por day: until_ts + fails.
BACKOFF_MIN_SECONDS = 60 * 60        # 1h
BACKOFF_MAX_SECONDS = 6 * 60 * 60    # 6h

def _backoff_path(day: str) -> Path:
    return Path(f"/tmp/scheduler_backoff_{day}.json")

def _get_backoff(day: str) -> Dict[str, Any]:
    p = _backoff_path(day)
    if not p.exists():
        return {"until_ts": 0, "fails": 0}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            return {"until_ts": 0, "fails": 0}
        return {
            "until_ts": float(d.get("until_ts") or 0),
            "fails": int(d.get("fails") or 0),
        }
    except Exception:
        return {"until_ts": 0, "fails": 0}

def _set_backoff(day: str) -> Dict[str, Any]:
    st = _get_backoff(day)
    fails = int(st.get("fails") or 0) + 1
    # Exponencial suave: 1h, 2h, 4h, 6h (cap)
    seconds = min(BACKOFF_MAX_SECONDS, BACKOFF_MIN_SECONDS * (2 ** (fails - 1)))
    until_ts = time.time() + seconds
    out = {"until_ts": until_ts, "fails": fails}
    _backoff_path(day).write_text(json.dumps(out), encoding="utf-8")
    return out

def _clear_backoff(day: str) -> None:
    p = _backoff_path(day)
    if p.exists():
        try:
            p.unlink()
        except Exception:
            pass


def _load_contract(day: str) -> Dict[str, Any]:
    p = API_DATA_DIR / "contracts" / day / "contract.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _contract_has_any_picks(day: str) -> bool:
    c = _load_contract(day)
    if not isinstance(c, dict):
        return False
    pc = c.get("picks_classic") or []
    pp = c.get("picks_parlay_premium") or []
    pv = c.get("picks_value") or []
    return (isinstance(pc, list) and len(pc) > 0) or (isinstance(pp, list) and len(pp) > 0) or (isinstance(pv, list) and len(pv) > 0)

def _run_daily_pipeline(day: str) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)

    cmd = [sys.executable, "-u", str(REPO_ROOT / "api" / "scripts" / "daily_pipeline.py"), day]
    logger.info("RUN daily_pipeline: %s", " ".join(cmd))
    subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, check=True)

def init_scheduler(app=None):
    """
    Scheduler con dos fases:
    
    FASE 1 (6am exacto): Ejecuta pipeline completo (genera contrato + todos los picks)
    - Fetch odds UNA VEZ (cacheado por 6h)
    - Genera picks para 24h
    
    FASE 2 (cada 10 min): Solo actualiza live scores con otras APIs
    - NO re-ejecuta pipeline
    - Solo enriquece contratos existentes con datos live
    """
    import threading
    from datetime import datetime

    def is_6am_window() -> bool:
        """Check si estamos en la ventana de 6am (6:00-6:10)"""
        tz = pytz.timezone('Europe/Madrid')
        now = datetime.now(tz)
        hour = now.hour
        minute = now.minute
        # Ejecuta entre 6:00 y 6:10
        return hour == 6 and minute < 10
    
    def loop():
        last_pipeline_day = None
        
        # Import live_score_update dynamically to avoid import issues
        try:
            from services.live_score_update import update_contract_with_live_scores
        except ImportError:
            from api.services.live_score_update import update_contract_with_live_scores
        
        while True:
            day = cycle_day_str()  # 06:00 Europe/Madrid cycle
            lock_file = f"/tmp/scheduler_lock_{day}"
            
            # DF_BACKOFF_V1: si estamos en backoff, no reintentar todavía
            st = _get_backoff(day)
            until_ts = float(st.get('until_ts') or 0)
            if until_ts and time.time() < until_ts:
                logger.info('Scheduler: backoff active for %s until_ts=%s fails=%s; skip pipeline', day, int(until_ts), st.get('fails'))
                time.sleep(600)
                continue

            try:
                # FASE 1: Pipeline UNA SOLA VEZ a las 6am
                if is_6am_window() and last_pipeline_day != day:
                    if _contract_has_any_picks(day):
                        logger.info("Scheduler [6am check]: contract already non-empty for %s; skip", day)
                    else:
                        if os.path.exists(lock_file):
                            logger.info("Scheduler [6am check]: lock exists for %s; skip", day)
                        else:
                            try:
                                with open(lock_file, "w", encoding="utf-8") as f:
                                    f.write("locked")
                                logger.info("=== PIPELINE %s START (6am phase) ===", day)
                                _run_daily_pipeline(day)
                                logger.info("=== PIPELINE %s DONE (6am phase) ===", day)
                                last_pipeline_day = day
                                _clear_backoff(day)
                            finally:
                                if os.path.exists(lock_file):
                                    os.unlink(lock_file)
                
                # FASE 2: Actualizar live scores (cada 10 min si el contrato existe)
                if _contract_has_any_picks(day):
                    try:
                        result = update_contract_with_live_scores(day)
                        if result.get("updates_count", 0) > 0:
                            logger.info(f"Updated {result['updates_count']} live scores for {day}")
                    except Exception as e:
                        logger.debug(f"Live score update failed (non-critical): {e}")
                
            except Exception as e:
                st2 = _set_backoff(day)
                logger.exception("Scheduler loop error for day=%s: %s (backoff until_ts=%s fails=%s)", day, e, int(st2.get('until_ts') or 0), st2.get('fails'))

            time.sleep(600)  # 10 min

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    logger.info("Scheduler started (6am pipeline + 10min live updates; cycle=06:00 Europe/Madrid)")
