import logging
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

# Allow imports from src/ when running as  python src/main.py
sys.path.insert(0, os.path.dirname(__file__))

from transform.schema import init_schema
from ingest.ingest_noise import run as run_noise
from ingest.ingest_schedule import run as run_schedule
from ingest.ingest_weather import run as run_weather
from dashboard.app import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

NOISE_INTERVAL_HOURS    = int(os.getenv("NOISE_INTERVAL_HOURS",    "1"))
SCHEDULE_INTERVAL_HOURS = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "1"))
WEATHER_INTERVAL_HOURS  = int(os.getenv("WEATHER_INTERVAL_HOURS",  "1"))
DASH_PORT = int(os.getenv("DASH_PORT", "8050"))


def _safe(fn):
    """Wrap a job function so exceptions are logged but don't crash the scheduler."""
    def wrapper():
        try:
            fn()
        except Exception as exc:
            log.error("Job %s failed: %s", fn.__name__, exc, exc_info=True)
    wrapper.__name__ = fn.__name__
    return wrapper


if __name__ == "__main__":
    log.info("Initialising schema and data directories")
    init_schema()

    # Run each ingest job once at startup so the dashboard has data immediately
    log.info("Running initial ingestion")
    _safe(run_schedule)()
    _safe(run_weather)()
    _safe(run_noise)()

    scheduler = BackgroundScheduler()
    scheduler.add_job(_safe(run_noise),    "interval", hours=NOISE_INTERVAL_HOURS,    id="noise")
    scheduler.add_job(_safe(run_schedule), "interval", hours=SCHEDULE_INTERVAL_HOURS, id="schedule")
    scheduler.add_job(_safe(run_weather),  "interval", hours=WEATHER_INTERVAL_HOURS,  id="weather")
    scheduler.start()
    log.info(
        "Scheduler started — noise/schedule/weather every %d/%d/%d h",
        NOISE_INTERVAL_HOURS, SCHEDULE_INTERVAL_HOURS, WEATHER_INTERVAL_HOURS,
    )

    log.info("Starting Dash server on port %d", DASH_PORT)
    app.run(host="0.0.0.0", port=DASH_PORT, debug=False)
