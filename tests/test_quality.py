"""
Data quality tests — run with:  pytest tests/test_quality.py -v

These tests query the live DuckDB file. They skip automatically when the
database does not yet exist, so they are safe to run at any pipeline stage.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

DB_PATH = os.getenv("DB_PATH", "data/nursipalu.duckdb")


@pytest.fixture(scope="session")
def conn():
    if not Path(DB_PATH).exists():
        pytest.skip(f"Database not found at {DB_PATH} — run the pipeline first")
    import duckdb
    return duckdb.connect(DB_PATH, read_only=True)


# ---------------------------------------------------------------------------
# noise table
# ---------------------------------------------------------------------------

def test_not_null_timestamp_noise(conn):
    """Every noise row must have a non-null timestamp_utc."""
    count = conn.execute(
        "SELECT COUNT(*) FROM noise WHERE timestamp_utc IS NULL"
    ).fetchone()[0]
    assert count == 0, f"{count} noise rows have NULL timestamp_utc"


def test_unique_station_timestamp(conn):
    """No station should have more than one row per timestamp."""
    dups = conn.execute("""
        SELECT station_id, timestamp_utc, COUNT(*) AS n
        FROM noise
        GROUP BY station_id, timestamp_utc
        HAVING COUNT(*) > 1
    """).fetchall()
    assert not dups, f"Duplicate (station_id, timestamp_utc) rows found: {dups[:5]}"


def test_noise_laf_eq_range(conn):
    """LAFeq values must be in a physically realistic 0–150 dB range."""
    bad = conn.execute(
        "SELECT COUNT(*) FROM noise WHERE laf_eq_db < 0 OR laf_eq_db > 150"
    ).fetchone()[0]
    assert bad == 0, f"{bad} noise rows have laf_eq_db outside 0–150 dB"


def test_noise_lceq_range(conn):
    """LCeq values must be in a physically realistic 0–160 dB range."""
    bad = conn.execute(
        "SELECT COUNT(*) FROM noise "
        "WHERE lceq_db IS NOT NULL AND (lceq_db < 0 OR lceq_db > 160)"
    ).fetchone()[0]
    assert bad == 0, f"{bad} noise rows have lceq_db outside 0–160 dB"


def test_noise_data_completeness(conn):
    """Data completeness percentage must be between 0 and 100."""
    bad = conn.execute(
        "SELECT COUNT(*) FROM noise "
        "WHERE cntp IS NOT NULL AND (cntp < 0 OR cntp > 100)"
    ).fetchone()[0]
    assert bad == 0, f"{bad} noise rows have cntp outside 0–100 %"


def test_noise_peak_gte_eq(conn):
    """Peak levels must be >= equivalent levels (a physical constraint)."""
    bad = conn.execute("""
        SELECT COUNT(*) FROM noise
        WHERE la_max_db IS NOT NULL AND laeq_db IS NOT NULL
          AND la_max_db < laeq_db
    """).fetchone()[0]
    assert bad == 0, f"{bad} rows have la_max_db < laeq_db (peak below average)"


# ---------------------------------------------------------------------------
# schedule table
# ---------------------------------------------------------------------------

def test_schedule_start_before_end(conn):
    """Every schedule entry must have start before end."""
    bad = conn.execute(
        "SELECT COUNT(*) FROM schedule WHERE activity_start_utc >= activity_end_utc"
    ).fetchone()[0]
    assert bad == 0, f"{bad} schedule rows have start >= end"


def test_not_null_timestamp_schedule(conn):
    """Schedule rows must have non-null start and end timestamps."""
    bad = conn.execute(
        "SELECT COUNT(*) FROM schedule "
        "WHERE activity_start_utc IS NULL OR activity_end_utc IS NULL"
    ).fetchone()[0]
    assert bad == 0, f"{bad} schedule rows have NULL timestamps"


# ---------------------------------------------------------------------------
# weather table
# ---------------------------------------------------------------------------

def test_not_null_timestamp_weather(conn):
    """Every weather row must have a non-null timestamp_utc."""
    count = conn.execute(
        "SELECT COUNT(*) FROM weather WHERE timestamp_utc IS NULL"
    ).fetchone()[0]
    assert count == 0, f"{count} weather rows have NULL timestamp_utc"


def test_weather_value_range(conn):
    """Sanity-check Open-Meteo weather values against physically plausible bounds."""
    checks = [
        ("wind_speed",    "wind_speed < 0 OR wind_speed > 100",   "wind speed outside 0–100 m/s"),
        ("temperature",   "temperature < -60 OR temperature > 60", "temperature outside -60–60 °C"),
        ("pressure",      "pressure < 870 OR pressure > 1085",     "pressure outside 870–1085 hPa"),
        ("cloud_cover",   "cloud_cover < 0 OR cloud_cover > 100",  "cloud cover outside 0–100 %"),
        ("precipitation", "precipitation < 0",                      "negative precipitation"),
    ]
    for col, condition, label in checks:
        non_null = conn.execute(
            f"SELECT COUNT(*) FROM weather WHERE {col} IS NOT NULL"
        ).fetchone()[0]
        if non_null == 0:
            continue
        bad = conn.execute(
            f"SELECT COUNT(*) FROM weather WHERE {condition}"
        ).fetchone()[0]
        assert bad == 0, f"{bad} weather rows have {label}"
