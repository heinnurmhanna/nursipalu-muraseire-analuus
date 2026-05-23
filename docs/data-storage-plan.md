# Data Storage Plan

Reference document for structuring, naming, and formatting all data files in this pipeline. Consult this before writing any ingestion, transformation, or quality script.

---

## Folder layout

```
data/
├── raw/
│   ├── noise/          ← unmodified downloads from noise API, one file per fetch run
│   ├── schedule/       ← unmodified schedule JSON snapshots
│   └── weather/        ← unmodified weather API responses
├── staged/
│   ├── noise/          ← normalized intermediate CSV per source
│   ├── schedule/       ← normalized intermediate CSV per source
│   └── weather/        ← normalized intermediate CSV per source
└── processed/
    └── merged/         ← unified analytic dataset (Parquet)
```

The `data/` directory is gitignored. Never commit data files.

---

## File naming convention

All raw and staged files use a timestamp suffix so that each fetch run is preserved and no file is ever overwritten:

```
{source}_{YYYYMMDD_HHMMSS}.{ext}

Examples:
  data/raw/noise/noise_20260519_143000.json
  data/staged/schedule/schedule_20260519_143000.csv
  data/processed/merged/merged_20260519_143000.parquet
```

---

## File formats

| Layer | Format | Reason |
|---|---|---|
| Raw | CSV or JSON (source-native) | Preserve original structure without conversion |
| Staged | CSV | Human-readable, easy to inspect and diff |
| Processed / merged | Parquet | Fast column filtering; efficient for dashboard queries |

---

## Staged record schema

Every file in `data/staged/` must include these four fields, regardless of source:

| Field | Type | Description |
|---|---|---|
| `source_id` | string | Identifies the source (`noise`, `schedule`, `weather`) |
| `original_timestamp` | string | Timestamp as it appeared in the raw source |
| `timestamp_utc` | datetime | Normalized to UTC, hourly granularity |
| `ingestion_run_at` | datetime | When the ingestion script fetched this record |

---

## Merged dataset schema

The file in `data/processed/merged/` is the single analytic table used by the dashboard and quality checks.

| Field | Type | Source |
|---|---|---|
| `timestamp_utc` | datetime | Common time index (hourly, UTC) |
| `avg_noise_db` | float | Noise |
| `max_noise_db` | float | Noise |
| `schedule_activity` | string / null | Schedule |
| `planned_noise_level` | string / null | Schedule |
| `wind_speed` | float | Weather |
| `wind_direction` | float | Weather |
| `temperature` | float | Weather |
| `pressure` | float | Weather |
| `cloud_cover` | float | Weather |
| `precipitation` | float | Weather |
| `noise_source_url` | string | Provenance |
| `schedule_snapshot` | string | Provenance — filename of the raw schedule file used |
| `weather_api_request` | string | Provenance — full API request URL used |

---

## Metadata sidecar files

Each dataset folder contains a `metadata.json` that is updated after every successful ingestion or transformation run.

```
data/raw/noise/metadata.json
data/raw/schedule/metadata.json
data/raw/weather/metadata.json
data/processed/merged/_metadata.json
```

Required fields:

```json
{
  "ingestion_time": "2026-05-19T14:30:00Z",
  "record_count": 1440,
  "quality_check_passed": true,
  "timezone_assumption": "UTC",
  "source_url": "https://noise.ellegroup.eu/public/1"
}
```

---

## Incremental update rule

Always write new files — never overwrite raw history. Use dated filenames (see naming convention above). If a merged Parquet file already exists for the same time window, append or replace only that window's rows; do not truncate the full file.

---

## Configuration rule

No hardcoded URLs or coordinates in scripts. All source endpoints and parameters are read from `.env` via `python-dotenv`. See `.env.example` for required keys.
