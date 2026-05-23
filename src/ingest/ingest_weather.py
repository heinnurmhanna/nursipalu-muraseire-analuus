"""
Open-Meteo weather data ingestion.

API: https://api.open-meteo.com/v1/forecast
Parameters read from .env: WEATHER_LATITUDE, WEATHER_LONGITUDE.
Fetches the past 7 days + 1 day ahead (hourly) to cover any gaps.
Rows already present in the DB (same timestamp_utc) are skipped via INSERT OR IGNORE
implemented with a NOT EXISTS sub-select.

Response structure:
  {
    "hourly": {
      "time":               ["2026-05-12T00:00", ...],  // local ISO without tz
      "temperature_2m":     [...],
      "wind_speed_10m":     [...],
      "wind_direction_10m": [...],
      "surface_pressure":   [...],
      "precipitation":      [...],
      "cloud_cover":        [...]
    }
  }
All times from Open-Meteo with timezone=UTC are already UTC.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from transform.schema import execute

load_dotenv()

BASE_URL = os.environ["WEATHER_SOURCE_URL"]
LAT = os.environ["WEATHER_LATITUDE"]
LON = os.environ["WEATHER_LONGITUDE"]
RAW_DIR = Path("data/raw/weather")
METADATA_FILE = RAW_DIR / "metadata.json"

HOURLY_PARAMS = ",".join([
    "temperature_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
    "precipitation",
    "cloud_cover",
])

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _build_url() -> str:
    return (
        f"{BASE_URL}?latitude={LAT}&longitude={LON}"
        f"&hourly={HOURLY_PARAMS}&timezone=UTC&past_days=7"
    )


def _update_metadata(count: int, request_url: str) -> None:
    meta = {
        "ingestion_time": datetime.now(timezone.utc).isoformat(),
        "record_count": count,
        "quality_check_passed": None,
        "timezone_assumption": "UTC",
        "source_url": request_url,
    }
    METADATA_FILE.write_text(json.dumps(meta, indent=2))


def run() -> None:
    request_url = _build_url()
    log.info("Fetching weather from %s", request_url)
    resp = requests.get(request_url, timeout=30)
    resp.raise_for_status()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_file = RAW_DIR / f"weather_{ts}.json"
    raw_file.write_text(resp.text, encoding="utf-8")
    log.info("Saved raw file: %s", raw_file)

    hourly = resp.json()["hourly"]
    times = hourly["time"]
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0

    for i, t in enumerate(times):
        timestamp_utc = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)

        # Skip if this hour is already stored
        existing = execute(
            "SELECT COUNT(*) FROM weather WHERE timestamp_utc = ?", [timestamp_utc]
        ).fetchone()[0]
        if existing:
            continue

        execute(
            "INSERT INTO weather "
            "(ingested_at, timestamp_utc, wind_speed, wind_direction, temperature, "
            " pressure, cloud_cover, precipitation, api_request_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                now,
                timestamp_utc,
                hourly["wind_speed_10m"][i],
                hourly["wind_direction_10m"][i],
                hourly["temperature_2m"][i],
                hourly["surface_pressure"][i],
                hourly["cloud_cover"][i],
                hourly["precipitation"][i],
                request_url,
            ],
        )
        inserted += 1

    log.info("Inserted %d new weather rows", inserted)
    _update_metadata(inserted, request_url)


if __name__ == "__main__":
    from transform.schema import init_schema
    init_schema()
    run()
