# Nexus AI Daily API (MVP)

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m app.ingest --tz Asia/Hong_Kong --days 7
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /api/health`
- `GET /api/editions?tz=Asia/Hong_Kong&days=7`
- `GET /api/editions/{YYYY-MM-DD}?tz=Asia/Hong_Kong`
- `GET /api/items/{id}`

## Edition semantics

For a local label date `X`, the edition window is the previous UTC day (`UTC_day(X-1)`, `00:00:00` → `23:59:59`).
