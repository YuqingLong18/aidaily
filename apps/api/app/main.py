from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

from app.db import init_db, session_scope
from app.models import Section
from app.repo import get_item, list_items_for_edition, top_by_section
from app.schemas import EditionMetaOut, EditionOut, ItemOut
from app.time_semantics import edition_window_for_local_date, local_today


app = FastAPI(title="Nexus AI Daily API (MVP)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/", include_in_schema=False)
def root() -> HTMLResponse:
    return HTMLResponse(
        """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Nexus AI Daily API</title>
    <style>
      body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial;margin:40px;line-height:1.5}
      code{background:#f4f4f5;padding:2px 6px;border-radius:6px}
      a{color:#2563eb;text-decoration:none} a:hover{text-decoration:underline}
      .box{background:#fafafa;border:1px solid #e5e7eb;border-radius:12px;padding:16px;max-width:760px}
      ul{margin:8px 0 0 18px}
    </style>
  </head>
  <body>
    <h2>Nexus AI Daily API (MVP)</h2>
    <div class="box">
      <div>Try:</div>
      <ul>
        <li><a href="/docs"><code>/docs</code></a> (Swagger UI)</li>
        <li><a href="/api/health"><code>/api/health</code></a></li>
        <li><a href="/api/editions?tz=Asia%2FHong_Kong&days=7"><code>/api/editions?tz=Asia/Hong_Kong&amp;days=7</code></a></li>
      </ul>
      <div style="margin-top:12px;color:#6b7280">
        The web dashboard runs separately (default <code>http://localhost:3000</code>).
      </div>
    </div>
  </body>
</html>
""".strip()
    )


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/editions", response_model=list[EditionMetaOut])
def list_editions(
    tz: str = Query(default="Asia/Hong_Kong"),
    days: int = Query(default=7, ge=1, le=14),
) -> list[EditionMetaOut]:
    today = local_today(tz)
    dates = [today.fromordinal(today.toordinal() - i) for i in range(days)]

    out: list[EditionMetaOut] = []
    with session_scope() as session:
        for d in dates:
            window = edition_window_for_local_date(d, tz)
            edition_date_local = d.isoformat()
            items = list_items_for_edition(session, edition_date_local, tz)
            out.append(
                EditionMetaOut(
                    edition_date_local=edition_date_local,
                    edition_timezone=tz,
                    utc_date=window.utc_date.isoformat(),
                    utc_start=window.utc_start,
                    utc_end=window.utc_end,
                    item_count=len(items),
                )
            )
    return out


@app.get("/api/editions/{edition_date_local}", response_model=EditionOut)
def get_edition(
    edition_date_local: str,
    tz: str = Query(default="Asia/Hong_Kong"),
) -> EditionOut:
    try:
        d = date.fromisoformat(edition_date_local)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="edition_date_local must be YYYY-MM-DD") from e

    window = edition_window_for_local_date(d, tz)
    with session_scope() as session:
        items = list_items_for_edition(session, edition_date_local, tz)

    limit_by_section = {
        Section.ai_for_science: 5,
        Section.ai_theory_arch: 5,
        Section.ai_education: 5,
        Section.product_tech: 6,
        Section.market_policy: 5,
    }
    grouped = top_by_section(items, limit_by_section)

    def to_out(item) -> ItemOut:
        tags = [t.strip() for t in (item.tags_csv or "").split(",") if t.strip()]
        bullets = [b.strip("- ").strip() for b in (item.summary_bullets_md or "").splitlines() if b.strip()]
        return ItemOut(
            id=item.id,
            item_type=item.item_type,
            section=item.section,
            title=item.title,
            source=item.source,
            source_url=item.source_url,
            canonical_url=item.canonical_url,
            published_at_utc=item.published_at_utc,
            edition_date_local=item.edition_date_local,
            edition_timezone=item.edition_timezone,
            tags=tags,
            difficulty=item.difficulty,
            summary_bullets=bullets,
            why_it_matters=item.why_it_matters_md or None,
            market_impact=item.market_impact_md or None,
            source_reliability=item.source_reliability,
            timestamp_precision=item.timestamp_precision,
            timestamp_confidence=item.timestamp_confidence,
            rank_score=item.rank_score,
        )

    sections_out = {section: [to_out(i) for i in grouped.get(section, [])] for section in Section}
    return EditionOut(
        edition_date_local=edition_date_local,
        edition_timezone=tz,
        utc_date=window.utc_date.isoformat(),
        utc_start=window.utc_start,
        utc_end=window.utc_end,
        sections=sections_out,
    )


@app.get("/api/items/{item_id}", response_model=ItemOut)
def item_detail(item_id: str, tz: Optional[str] = None) -> ItemOut:
    from uuid import UUID

    try:
        uid = UUID(item_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="invalid item id") from e

    with session_scope() as session:
        item = get_item(session, uid)
        if item is None:
            raise HTTPException(status_code=404, detail="not found")

    tags = [t.strip() for t in (item.tags_csv or "").split(",") if t.strip()]
    bullets = [b.strip("- ").strip() for b in (item.summary_bullets_md or "").splitlines() if b.strip()]
    return ItemOut(
        id=item.id,
        item_type=item.item_type,
        section=item.section,
        title=item.title,
        source=item.source,
        source_url=item.source_url,
        canonical_url=item.canonical_url,
        published_at_utc=item.published_at_utc,
        edition_date_local=item.edition_date_local,
        edition_timezone=item.edition_timezone if tz is None else tz,
        tags=tags,
        difficulty=item.difficulty,
        summary_bullets=bullets,
        why_it_matters=item.why_it_matters_md or None,
        market_impact=item.market_impact_md or None,
        source_reliability=item.source_reliability,
        timestamp_precision=item.timestamp_precision,
        timestamp_confidence=item.timestamp_confidence,
        rank_score=item.rank_score,
    )
