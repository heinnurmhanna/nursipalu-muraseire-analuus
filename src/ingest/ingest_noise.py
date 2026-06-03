"""
Noise monitoring data ingestion.

API: https://noise.ellegroup.eu/api/stations/1/value1h
     ?from_datetime=<YYYY-MM-DDTHH:MM:SS.mmmZ>&to_datetime=<YYYY-MM-DDTHH:MM:SS.mmmZ>

Response: flat JSON array, one row per hour.
Fields stored:
  Acoustic: laeq_db (la_eq), la_max_db, lceq_db (lc_eq), lc_peak_db, lzeq_db (lz_eq), lz_peak_db
  Quality:  cnt, cntm, cntp  (filter rows with cntp < 90 in analysis)
  Weather:  temperature_c, pressure_hpa, rain_mm, humidity_pct, wind_direction_deg, wind_speed_ms

Gap-fill behaviour:
  Each run fetches the last 24 hours. Only rows strictly newer than the latest DB
  timestamp are inserted. Accepts gaps > 24h and logs a warning.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

from transform.schema import execute, executemany

load_dotenv()

NOISE_BASE_URL = "https://noise.ellegroup.eu/api/stations/1/value1h"
RAW_DIR = Path("data/raw/noise")
METADATA_FILE = RAW_DIR / "metadata.json"
STATION_ID = "nursipalu_1"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _fmt(dt: datetime) -> str:
    """Format a UTC datetime as required by the API: 2026-05-20T14:17:12.000Z"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _build_url(from_dt: datetime, to_dt: datetime) -> str:
    return f"{NOISE_BASE_URL}?from_datetime={_fmt(from_dt)}&to_datetime={_fmt(to_dt)}"


def _parse_ts(data_ts: str) -> datetime:
    """Convert "2026-05-19 14:00:00" (UTC, space-separated) to a UTC datetime."""
    return datetime.strptime(data_ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _float(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _int(v) -> int | None:
    try:
        return int(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def _latest_db_timestamp() -> datetime | None:
    """Return the most recent timestamp_utc stored for this station, or None if empty."""
    row = execute(
        "SELECT MAX(timestamp_utc) FROM noise WHERE station_id = ?",
        [STATION_ID],
    ).fetchone()
    if row is None or row[0] is None:
        return None
    val = row[0]
    if isinstance(val, str):
        val = datetime.fromisoformat(val.replace("Z", "+00:00"))
    return val if val.tzinfo is not None else val.replace(tzinfo=timezone.utc)


def _update_metadata(count: int, source_url: str) -> None:
    meta = {
        "ingestion_time": datetime.now(timezone.utc).isoformat(),
        "record_count": count,
        "quality_check_passed": None,
        "timezone_assumption": "UTC",
        "source_url": source_url,
    }
    METADATA_FILE.write_text(json.dumps(meta, indent=2))


def run() -> None:
    to_dt = datetime.now(timezone.utc)
    from_dt = to_dt - timedelta(days=1)
    source_url = _build_url(from_dt, to_dt)

    log.info("Fetching noise data from %s to %s", _fmt(from_dt), _fmt(to_dt))
    resp = requests.get(source_url, timeout=30)
    resp.raise_for_status()

    ts_str = to_dt.strftime("%Y%m%d_%H%M%S")
    raw_file = RAW_DIR / f"noise_{ts_str}.json"
    raw_file.write_text(resp.text, encoding="utf-8")
    log.info("Saved raw file: %s", raw_file)

    data = resp.json()
    if not isinstance(data, list) or not data:
        log.warning("Empty or unexpected response: %s", str(data)[:200])
        _update_metadata(0, source_url)
        return

    parsed = []
    for row in data:
        ts_raw = row.get("data_ts")
        la_eq = row.get("la_eq")
        if ts_raw is None or la_eq is None:
            continue
        parsed.append({
            "timestamp_dt":       _parse_ts(ts_raw),
            "cnt":                _int(row.get("cnt")),
            "cntm":               _int(row.get("cntm")),
            "cntp":               _float(row.get("cntp")),
            "laeq_db":            _float(la_eq),
            "laf_eq_db":          _float(row.get("laf_eq")),
            "la_max_db":          _float(row.get("la_max")),
            "lceq_db":            _float(row.get("lc_eq")),
            "lc_peak_db":         _float(row.get("lc_peak")),
            "lzeq_db":            _float(row.get("lz_eq")),
            "lz_peak_db":         _float(row.get("lz_peak")),
            "temperature_c":      _float(row.get("wz_temp")),
            "pressure_hpa":       _float(row.get("wz_pres")),
            "rain_mm":            _float(row.get("wz_rain")),
            "humidity_pct":       _float(row.get("wz_humid")),
            "wind_direction_deg": _float(row.get("wz_wind_d")),
            "wind_speed_ms":      _float(row.get("wz_wind_s")),
        })

    if not parsed:
        log.warning("No parseable rows in response")
        _update_metadata(0, source_url)
        return

    latest_in_db = _latest_db_timestamp()

    if latest_in_db is None:
        cutoff = None
        log.info("Empty DB — inserting all %d fetched rows", len(parsed))
    elif latest_in_db < from_dt:
        cutoff = None
        log.warning(
            "Gap detected: latest DB record is %s, fetch window starts at %s — inserting all fetched rows",
            latest_in_db.isoformat(), _fmt(from_dt),
        )
    else:
        cutoff = latest_in_db
        log.info("Latest DB timestamp: %s — inserting rows after that", latest_in_db.isoformat())

    now = datetime.now(timezone.utc).isoformat()
    new_rows = [
        (
            now,
            r["timestamp_dt"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            STATION_ID,
            r["cnt"],
            r["cntm"],
            r["cntp"],
            r["laeq_db"],
            r["laf_eq_db"],
            r["la_max_db"],
            r["lceq_db"],
            r["lc_peak_db"],
            r["lzeq_db"],
            r["lz_peak_db"],
            r["temperature_c"],
            r["pressure_hpa"],
            r["rain_mm"],
            r["humidity_pct"],
            r["wind_direction_deg"],
            r["wind_speed_ms"],
            source_url,
            str(raw_file),
        )
        for r in parsed
        if cutoff is None or r["timestamp_dt"] > cutoff
    ]

    if new_rows:
        executemany(
            "INSERT INTO noise ("
            "  ingested_at, timestamp_utc, station_id,"
            "  cnt, cntm, cntp,"
            "  laeq_db, laf_eq_db, la_max_db, lceq_db, lc_peak_db, lzeq_db, lz_peak_db,"
            "  temperature_c, pressure_hpa, rain_mm, humidity_pct,"
            "  wind_direction_deg, wind_speed_ms,"
            "  source_url, raw_file"
            ") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            new_rows,
        )
        log.info("Inserted %d new rows (%d already covered)", len(new_rows), len(parsed) - len(new_rows))
    else:
        log.info(
            "No new rows — DB already up to date (latest: %s)",
            latest_in_db.isoformat() if latest_in_db else "—",
        )

    _update_metadata(len(new_rows), source_url)


if __name__ == "__main__":
    from transform.schema import init_schema
    init_schema()
    run()
