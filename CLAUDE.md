# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in any overrides
```

All source URLs and coordinates are read from `.env` via `python-dotenv`. Never hardcode endpoints in scripts.

## Running with Docker (recommended)

```bash
docker compose up --build        # build image and start
docker compose up                # start after first build
docker compose down              # stop
```

Dashboard available at http://localhost:8050 once the first ingest run completes (~30 s after startup).

## Running locally without Docker

```bash
# Requires PYTHONPATH so intra-src imports resolve
PYTHONPATH=src python src/main.py          # full pipeline + dashboard

# Individual scripts (also need PYTHONPATH)
PYTHONPATH=src python src/ingest/ingest_schedule.py
PYTHONPATH=src python src/ingest/ingest_weather.py
PYTHONPATH=src python src/ingest/ingest_noise.py
PYTHONPATH=src python src/dashboard/app.py
```

## Tests

```bash
pytest tests/                    # all tests
pytest tests/test_quality.py     # single file
pytest tests/ -k "test_noise"    # single test by name
```

Tests query the live DuckDB file. They skip automatically if the DB does not yet exist.

## Architecture

`src/main.py` is the single entry point. It initialises the DuckDB schema, fires each ingest job once at startup, then starts APScheduler (background threads) and the Dash server (foreground).

```
src/main.py
  ├── transform/schema.py   — DuckDB connection, thread lock, CREATE TABLE/VIEW
  ├── ingest/ingest_noise.py    — fetches noise API → data/raw/noise/ + noise table
  ├── ingest/ingest_schedule.py — fetches schedule JSON (hash-checked) → schedule table
  ├── ingest/ingest_weather.py  — fetches Open-Meteo → data/raw/weather/ + weather table
  └── dashboard/app.py          — Dash app, reads from merged VIEW in DuckDB
```

All three tables are joined in a DuckDB `VIEW` called `merged` (hourly time index, UTC). The dashboard queries `merged` directly — no separate transform step needed.

DuckDB threading: one shared connection protected by `threading.Lock` in `schema.py`. Dash and APScheduler jobs share this connection inside the same process.

## Data storage conventions

See `docs/data-storage-plan.md` for the full spec. Key rules:

- **Filenames**: `{source}_{YYYYMMDD_HHMMSS}.{ext}` — never overwrite; always append a new file per run.
- **Formats**: raw → JSON/CSV, staged → CSV, merged → Parquet.
- **Every staged record** must include `source_id`, `original_timestamp`, `timestamp_utc`, `ingestion_run_at`.
- **Every merged row** must include provenance fields: `noise_source_url`, `schedule_snapshot`, `weather_api_request`.
- Each data folder gets a `metadata.json` sidecar updated after every successful run.

## Business question

Whether scheduled Nursipalu training ground activities and concurrent weather conditions correlate with measured noise level increases. The pipeline does not assert causation — it assesses whether time-based comparison of these three public sources produces interpretable results.
