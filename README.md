# Nexus AI Daily (MVP)

Desktop-first daily AI intelligence dashboard with the PRD’s edition semantics:

- The UI shows 7 local-day tabs (`Today … Today-6`) in a chosen timezone (default `Asia/Hong_Kong`).
- Each tab date `X` summarizes items published in the previous UTC day (`UTC_day(X-1)`).
- The UI discloses: “Edition date: X (summarizes UTC X-1)”.

## Quickstart

### 1) Backend (FastAPI)

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# ingest real sources for the edition window (default: live)
python -m app.ingest --tz Asia/Hong_Kong --days 1 --print-window

# optional: enable LLM curation (OpenRouter) to pick top items + generate tags/summaries
# Put these in `.env` (repo root or `apps/api/.env`):
# OPENROUTER_API_KEY="..."
# NEXUS_LLM_MODEL="google/gemini-2.5-flash"
python -m app.ingest --tz Asia/Hong_Kong --days 1 --curate

# (still available) create deterministic sample editions
python -m app.ingest --mode seed --tz Asia/Hong_Kong --days 7

uvicorn app.main:app --reload --port 8000
```

API base: `http://localhost:8000/api`

### 2) Frontend (Next.js)

```bash
cd apps/web
npm install
npm run dev
```

Open: `http://localhost:3000`

Set API base if needed:

```bash
export NEXT_PUBLIC_API_BASE="http://localhost:8000"
```

## Notes

- Storage defaults to SQLite at `apps/api/data/nexus.db` (override with `DATABASE_URL`).
- Live ingestion pulls from arXiv + industry RSS feeds; configure sources via env vars like `NEXUS_INDUSTRY_FEEDS`.
- LLM curation uses OpenRouter (`OPENROUTER_API_KEY`) and updates DB fields for tags, summaries, why-it-matters/market-impact, and ranking.
