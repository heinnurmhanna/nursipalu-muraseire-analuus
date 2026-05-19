# AI Agent Instructions

## Project overview
This repository is a data workflow for comparing Nursipalu noise monitoring, military training schedule data, and weather observations.
The goal is to ingest public data sources, clean and align them on a common timeline, evaluate data quality, and build a dashboard that helps answer whether scheduled activities and weather conditions correlate with measured noise increases.

## What to do first
- Use `README.md` as the primary source of truth for project scope and data sources.
- The repository currently contains planning documentation only, not implementation code.
- Start by creating a reproducible project structure such as:
  - `src/ingest/`
  - `src/transform/`
  - `src/quality/`
  - `src/dashboard/`
  - `data/`
  - `tests/`
- Prefer Python for scripts, since the README suggests `requirements.txt` and a data workflow architecture.

## Key tasks for the agent
- Implement data ingestion scripts for noise, schedule, and weather sources.
- Normalize timestamps, time zones, and temporal granularity across datasets.
- Merge data into a single analytic dataset suitable for comparison.
- Add data quality checks and tests for timestamp completeness, uniqueness, realistic ranges, and schedule validity.
- Build a dashboard or report that compares noise levels with scheduled activity periods and selected weather measures.

## Important constraints
- Do not invent a backend or frontend framework unless the repository already contains one.
- Keep the pipeline automated and repeatable using configuration files like `.env` or `requirements.txt`.
- Document assumptions and data source structure clearly in code comments and README updates.

## Useful reference
- `README.md` contains the project description, business question, expected data sources, and suggested workflow.
