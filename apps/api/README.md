# Nexus AI Daily API (MVP)

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m app.ingest --tz Asia/Hong_Kong --days 7
uvicorn app.main:app --reload --port 8000
```

## Manual ingestion for a specific edition date

Run ingestion “as if today is `2025-12-17` / `2025-12-18`” by explicitly setting the local edition date(s).

```bash
# Ingest two editions: 2025-12-18 and 2025-12-17 (HK local labels)
python -m app.ingest --tz Asia/Hong_Kong --date 2025-12-18 --days 2 --print-window

# Or: specify the dates directly (order doesn't matter)
python -m app.ingest --tz Asia/Hong_Kong --dates 2025-12-17,2025-12-18 --print-window
```

## Curation (prepare for frontend)

Ingestion fetches/stores items, but the frontend expects curated fields like `rank_score`, `tags`, `summary_bullets`, and (optionally) Chinese translations. Curation fills those via an LLM.

Prereq: set `OPENROUTER_API_KEY` (or `NEXUS_OPENROUTER_API_KEY`) in your environment.

```bash
# Curate already-ingested editions
python -m app.curate --tz Asia/Hong_Kong --dates 2025-12-17,2025-12-18

# Or do it in one step (ingest + curate)
python -m app.ingest --tz Asia/Hong_Kong --dates 2025-12-17,2025-12-18 --curate
```

## Endpoints

- `GET /api/health`
- `GET /api/editions?tz=Asia/Hong_Kong&days=7`
- `GET /api/editions/{YYYY-MM-DD}?tz=Asia/Hong_Kong`
- `GET /api/items/{id}`

## Edition semantics

For a local label date `X`, the edition window is the previous UTC day (`UTC_day(X-1)`, `00:00:00` → `23:59:59`).
