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
    """Inicializa un loop simple (cada 10 min) que asegura el contract del cycle day."""
    import threading

    def loop():
        while True:
            day = cycle_day_str()  # 06:00 Europe/Madrid cycle
            lock_file = f"/tmp/scheduler_lock_{day}"

            try:
                if _contract_has_any_picks(day):
                    logger.info("Scheduler: contract already non-empty for %s; skip", day)
                else:
                    if os.path.exists(lock_file):
                        logger.info("Scheduler: lock exists for %s; skip", day)
                    else:
                        try:
                            with open(lock_file, "w", encoding="utf-8") as f:
                                f.write("locked")
                            logger.info("=== PIPELINE %s START ===", day)
                            _run_daily_pipeline(day)
                            logger.info("=== PIPELINE %s DONE ===", day)
                        finally:
                            if os.path.exists(lock_file):
                                os.unlink(lock_file)
            except Exception as e:
                logger.exception("Scheduler loop error for day=%s: %s", day, e)

            time.sleep(600)  # 10 min

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    logger.info("Scheduler started (loop every 10 min; cycle=06:00 Europe/Madrid)")
