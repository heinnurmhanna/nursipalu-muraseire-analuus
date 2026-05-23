import logging
import os
import threading
from pathlib import Path

import duckdb

DB_PATH = os.getenv("DB_PATH", "data/nursipalu.duckdb")

log = logging.getLogger(__name__)

_NOISE_REQUIRED_COLS = {"cntp", "lceq_db", "lzeq_db", "lc_peak_db", "lz_peak_db", "wind_speed_ms"}


def _migrate_noise(conn: duckdb.DuckDBPyConnection) -> None:
    """Drop the noise table if it predates the current schema."""
    try:
        existing = {
            row[0]
            for row in conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'noise'"
            ).fetchall()
        }
    except Exception:
        return
    if existing and not _NOISE_REQUIRED_COLS.issubset(existing):
        log.warning("noise table has outdated schema — dropping and recreating (data will be re-fetched)")
        conn.execute("DROP TABLE noise")

_lock = threading.Lock()
_conn: duckdb.DuckDBPyConnection | None = None


def get_conn() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        _conn = duckdb.connect(DB_PATH)
    return _conn


def execute(sql: str, params: list | None = None):
    with _lock:
        conn = get_conn()
        return conn.execute(sql, params or [])


def executemany(sql: str, rows: list[list | tuple]):
    with _lock:
        conn = get_conn()
        conn.executemany(sql, rows)


def query_df(sql: str):
    with _lock:
        return get_conn().execute(sql).df()


def init_schema() -> None:
    for folder in [
        "data/raw/noise", "data/raw/schedule", "data/raw/weather",
        "data/staged/noise", "data/staged/schedule", "data/staged/weather",
        "data/processed/merged",
    ]:
        Path(folder).mkdir(parents=True, exist_ok=True)

    with _lock:
        conn = get_conn()
        _migrate_noise(conn)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS noise (
                ingested_at          TIMESTAMPTZ NOT NULL,
                timestamp_utc        TIMESTAMPTZ NOT NULL,
                station_id           VARCHAR,

                -- Data quality (filter cntp < 90 to exclude incomplete intervals)
                cnt                  INTEGER,
                cntm                 INTEGER,
                cntp                 DOUBLE,

                -- A-weighted: general audible noise, environmental standard
                laeq_db              DOUBLE,
                la_max_db            DOUBLE,

                -- C-weighted: heavy weapons, low-frequency sources
                lceq_db              DOUBLE,
                lc_peak_db           DOUBLE,   -- primary impulse/blast indicator

                -- Z-weighted (flat): raw total acoustic energy, strongest blast indicator
                lzeq_db              DOUBLE,
                lz_peak_db           DOUBLE,

                -- On-station weather (co-located with microphone, preferred over Open-Meteo)
                temperature_c        DOUBLE,
                pressure_hpa         DOUBLE,
                rain_mm              DOUBLE,
                humidity_pct         DOUBLE,
                wind_direction_deg   DOUBLE,   -- meteorological: direction wind comes FROM
                wind_speed_ms        DOUBLE,

                source_url           VARCHAR,
                raw_file             VARCHAR
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                ingested_at          TIMESTAMPTZ NOT NULL,
                snapshot_hash        VARCHAR,
                raw_file             VARCHAR,
                activity_start_utc   TIMESTAMPTZ NOT NULL,
                activity_end_utc     TIMESTAMPTZ NOT NULL,
                location             VARCHAR,
                exercise_type        VARCHAR,
                planned_noise_level  VARCHAR,
                status               VARCHAR
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                ingested_at     TIMESTAMPTZ NOT NULL,
                timestamp_utc   TIMESTAMPTZ NOT NULL,
                wind_speed      DOUBLE,
                wind_direction  DOUBLE,
                temperature     DOUBLE,
                pressure        DOUBLE,
                cloud_cover     DOUBLE,
                precipitation   DOUBLE,
                api_request_url VARCHAR
            )
        """)

        # Training ground bearing FROM the noise station: 310°–330° (centre ~320°).
        # Wind FROM that direction (NW) blows toward the station (SE) = downwind.
        # Downwind window: 320° ± 45° → 275°–360° and 0°–5°.
        # Upwind window:   opposite centre 140° ± 45° → 95°–185°.
        conn.execute("""
            CREATE OR REPLACE VIEW merged AS
            WITH sched_per_hour AS (
                SELECT
                    n.timestamp_utc                        AS hour_ts,
                    MAX(s.activity_start_utc) IS NOT NULL  AS has_scheduled_activity,
                    MAX(s.planned_noise_level)             AS planned_noise_level,
                    MAX(s.exercise_type)                   AS exercise_type
                FROM noise n
                LEFT JOIN schedule s
                    ON n.timestamp_utc BETWEEN s.activity_start_utc AND s.activity_end_utc
                GROUP BY n.timestamp_utc
            )
            SELECT
                n.timestamp_utc,
                n.station_id,

                -- Data quality
                (n.cntp >= 90)                                       AS valid_data,

                -- Scheduled activity
                sph.has_scheduled_activity,
                sph.planned_noise_level,
                sph.exercise_type,

                -- Acoustic measurements
                n.laeq_db,
                n.la_max_db,
                n.lceq_db,
                n.lc_peak_db,
                n.lzeq_db,
                n.lz_peak_db,

                -- Peak event: impulsive military noise indicator
                (
                    COALESCE(n.lc_peak_db >= 80, FALSE)
                    OR COALESCE(n.lz_peak_db >= 85, FALSE)
                    OR COALESCE(n.la_max_db  >= 65, FALSE)
                )                                                    AS peak_event,

                -- On-station weather (primary)
                n.temperature_c,
                n.pressure_hpa,
                n.rain_mm,
                n.humidity_pct,
                n.wind_direction_deg,
                n.wind_speed_ms,

                -- Open-Meteo as fallback when station weather is NULL
                COALESCE(n.wind_direction_deg, w.wind_direction)     AS wind_dir_final,
                COALESCE(n.wind_speed_ms,      w.wind_speed)         AS wind_speed_final,

                -- Wind direction relative to training ground
                CASE
                    WHEN n.wind_direction_deg IS NULL THEN NULL
                    WHEN (n.wind_direction_deg >= 275 AND n.wind_direction_deg <= 360)
                      OR  n.wind_direction_deg <= 5
                    THEN TRUE
                    ELSE FALSE
                END                                                  AS wind_from_training_ground,

                CASE
                    WHEN n.wind_direction_deg IS NULL THEN NULL
                    WHEN (n.wind_direction_deg >= 275 AND n.wind_direction_deg <= 360)
                      OR  n.wind_direction_deg <= 5
                    THEN 'downwind'
                    WHEN  n.wind_direction_deg >= 95
                      AND n.wind_direction_deg <= 185
                    THEN 'upwind'
                    ELSE 'crosswind'
                END                                                  AS downwind_category,

                -- Wind speed category
                CASE
                    WHEN n.wind_speed_ms IS NULL THEN NULL
                    WHEN n.wind_speed_ms < 1     THEN 'calm'
                    WHEN n.wind_speed_ms < 3     THEN 'light'
                    WHEN n.wind_speed_ms < 6     THEN 'moderate'
                    ELSE                              'strong'
                END                                                  AS wind_speed_bin,

                (n.rain_mm > 0)                                      AS rain_flag

            FROM noise n
            LEFT JOIN sched_per_hour sph ON n.timestamp_utc = sph.hour_ts
            LEFT JOIN weather w          ON n.timestamp_utc = w.timestamp_utc
        """)
