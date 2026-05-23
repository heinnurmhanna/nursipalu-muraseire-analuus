"""
Military training schedule ingestion.

Source: https://mil.ee/wp-content/uploads/training-grounds/training_ground_schedule.json
Structure (confirmed):
  Top-level array of monthly schedule objects.
  Each object: trainingAreaId, trainingAreaName, year, month, approvedAt, exercises[].
  Exercise fields: id, startDate, endDate, exerciseType, trainingObjects[], noiseLevel, status.
  Timestamps: ISO 8601 UTC (e.g. "2026-05-17T21:00:00Z").
  noiseLevels: ABSENT | LOW | AVERAGE | HIGH | VERY_HIGH.
  exerciseType: TACTICS | SHOOTING | BLASTING.

Only rows for NURSIPALU are ingested. New snapshots are skipped if the content hash
matches the last stored hash (i.e. the file has not changed).
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

from transform.schema import execute, query_df

load_dotenv()

SOURCE_URL = os.environ["SCHEDULE_SOURCE_URL"]
RAW_DIR = Path("data/raw/schedule")
METADATA_FILE = RAW_DIR / "metadata.json"
NURSIPALU_KEYWORD = "NURSIPALU"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _last_hash() -> str | None:
    try:
        df = query_df("SELECT snapshot_hash FROM schedule ORDER BY ingested_at DESC LIMIT 1")
        return df["snapshot_hash"].iloc[0] if not df.empty else None
    except Exception:
        return None


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
    log.info("Fetching schedule from %s", SOURCE_URL)
    resp = requests.get(SOURCE_URL, timeout=30)
    resp.raise_for_status()

    content_hash = hashlib.md5(resp.content).hexdigest()
    last = _last_hash()
    if content_hash == last:
        log.info("Schedule unchanged (hash %s) — skipping", content_hash)
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_file = RAW_DIR / f"schedule_{ts}.json"
    raw_file.write_text(resp.text, encoding="utf-8")
    log.info("Saved raw file: %s", raw_file)

    data: list[dict] = resp.json()
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0

    for area in data:
        if NURSIPALU_KEYWORD not in area.get("trainingAreaName", "").upper():
            continue
        location = area["trainingAreaName"]
        for ex in area.get("exercises", []):
            start = ex.get("startDate")
            end = ex.get("endDate")
            if not start or not end:
                continue
            execute(
                "INSERT INTO schedule "
                "(ingested_at, snapshot_hash, raw_file, activity_start_utc, activity_end_utc, "
                " location, exercise_type, planned_noise_level, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    now,
                    content_hash,
                    str(raw_file),
                    start,
                    end,
                    location,
                    ex.get("exerciseType"),
                    ex.get("noiseLevel"),
                    ex.get("status"),
                ],
            )
            inserted += 1

    log.info("Inserted %d schedule rows (hash %s)", inserted, content_hash)
    _update_metadata(inserted, SOURCE_URL)


if __name__ == "__main__":
    from transform.schema import init_schema
    init_schema()
    run()
