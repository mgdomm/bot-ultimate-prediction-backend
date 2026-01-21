import os, sys, subprocess
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
from api.utils.cycle_day import cycle_day_str

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

REPO = Path(__file__).resolve().parents[2]
TZ = ZoneInfo(os.getenv("APP_TZ", "Europe/Madrid"))

def _ts():
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S %Z")

def _lock_path(day: str) -> Path:
    lock_dir = REPO / "api" / "data" / "locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return lock_dir / f"daily_pipeline_{day}.lock"

def _try_lock(day: str) -> bool:
    """
    Evita ejecuciones dobles (por reinicios/duplicados).
    Lock por día: si existe, no re-ejecuta.
    """
    lp = _lock_path(day)
    try:
        fd = os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"locked_at={_ts()}\n")
        return True
    except FileExistsError:
        return False

def run_daily_pipeline_job():
    day = cycle_day_str()  # 06:00 Europe/Madrid cycle
    print(f"[{_ts()}] SCHEDULER job fired for day={day}")

    if not _try_lock(day):
        print(f"[{_ts()}] SCHEDULER skip (lock exists): { _lock_path(day) }")
        return

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO)

    script = REPO / "api" / "scripts" / "daily_pipeline.py"
    cmd = [sys.executable, "-u", str(script), day]

    print(f"[{_ts()}] SCHEDULER running: {' '.join(cmd)}")
    # No check=True para no tumbar el scheduler si falla un día; logs quedan en stdout.
    p = subprocess.run(cmd, cwd=str(REPO), env=env)
    print(f"[{_ts()}] SCHEDULER finished rc={p.returncode}")

def init_scheduler(app=None):
    """
    Scheduler in-memory. En producción: 1 instancia del backend => 1 scheduler.
    Controlado por env ENABLE_INTERNAL_SCHEDULER=1
    """
    enabled = os.getenv("ENABLE_INTERNAL_SCHEDULER", "1").strip() in ("1", "true", "yes", "on")
    if not enabled:
        print(f"[{_ts()}] SCHEDULER disabled by env ENABLE_INTERNAL_SCHEDULER")
        return None

    hour = int(os.getenv("DAILY_PIPELINE_HOUR", "6"))
    minute = int(os.getenv("DAILY_PIPELINE_MINUTE", "0"))

    sched = BackgroundScheduler(timezone=TZ)
    trigger = CronTrigger(hour=hour, minute=minute, timezone=TZ)
    sched.add_job(run_daily_pipeline_job, trigger, id="daily_pipeline", replace_existing=True)

    sched.start()
    print(f"[{_ts()}] SCHEDULER started: daily at {hour:02d}:{minute:02d} {TZ}")

    # opcional: attach para shutdown
    if app is not None:
        try:
            app.state.scheduler = sched
        except Exception:
            pass
    return sched
