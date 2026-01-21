"""
Scheduler with cycle_day lock
Imports defensivos para Render (rootDir=api/ o repo_root)
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

def _robust_import(module_name):
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

odds_ingestion = _robust_import("services.odds_ingestion_multisport")
ingest_odds_for_day = odds_ingestion.ingest_odds_for_day

picks_parlay = _robust_import("services.picks_parlay_premium_multisport")
run_for_day = picks_parlay.run_for_day

logging.basicConfig(level=logging.INFO)

def init_scheduler(app=None):
    """Inicializa scheduler con ciclo diario fijo"""
    def daily_job():
        today = cycle_day_str()
        lock_file = f"/tmp/scheduler_lock_{today}"
        
        if os.path.exists(lock_file):
            logger.info(f"Lock existe para {today}, skip")
            return
            
        try:
            with open(lock_file, 'w') as f:
                f.write(str(datetime.now().timestamp()))
            
            logger.info(f"=== PIPELINE {today} INICIADO ===")
            ingest_odds_for_day(today)
            run_for_day(today)
            logger.info(f"=== PIPELINE {today} COMPLETADO ===")
            
        except Exception as e:
            logger.error(f"Pipeline fallo: {e}")
        finally:
            if os.path.exists(lock_file):
                os.unlink(lock_file)
    
    logger.info("Scheduler inicializado - ciclo 06:00 Madrid")
