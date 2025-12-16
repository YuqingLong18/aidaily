from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Optional

import feedparser
from urllib.parse import quote_plus

from app.http_client import fetch_text
from app.ingestion_types import RawIngestedItem
from app.models import ItemType, TimestampConfidence, TimestampPrecision
from app.time_semantics import EditionWindow
from app.url_utils import canonicalize_url


def _arxiv_query_for_window(categories: Iterable[str], window: EditionWindow) -> str:
    start = window.utc_start.strftime("%Y%m%d%H%M")
    end = window.utc_end.strftime("%Y%m%d%H%M")
    cats = " OR ".join([f"cat:{c}" for c in categories])
    return f"({cats}) AND submittedDate:[{start} TO {end}]"


def _to_dt_utc(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _arxiv_external_id(entry_id: str | None) -> str | None:
    if not entry_id:
        return None
    entry_id = entry_id.strip()
    if not entry_id:
        return None
    if "/" not in entry_id:
        return entry_id
    return entry_id.rsplit("/", 1)[-1]


def fetch_arxiv_items(
    window: EditionWindow,
    *,
    categories: List[str],
    max_results: int = 200,
) -> list[RawIngestedItem]:
    """
    Uses the arXiv API (Atom) and filters by submittedDate inside the UTC window.
    """
    if not categories:
        return []

    query = _arxiv_query_for_window(categories, window)
    query_qs = quote_plus(query)
    url = (
        "https://export.arxiv.org/api/query"
        f"?search_query={query_qs}"
        f"&start=0&max_results={max_results}"
        "&sortBy=submittedDate&sortOrder=descending"
    )
    parsed = feedparser.parse(fetch_text(url))

    out: list[RawIngestedItem] = []
    for entry in parsed.entries:
        title = " ".join((entry.get("title") or "").split())
        entry_id = entry.get("id") or None
        link = entry.get("link") or entry_id or ""
        source_url = canonicalize_url(link)

        published = _to_dt_utc(entry.get("published")) or _to_dt_utc(entry.get("updated"))
        if published is None:
            continue

        if published < window.utc_start or published > window.utc_end:
            continue

        summary = (entry.get("summary") or "").strip()
        tags = []
        for t in entry.get("tags") or []:
            term = (t.get("term") or "").strip()
            if term:
                tags.append(term)

        canonical = canonicalize_url(entry_id) if entry_id else None
        out.append(
            RawIngestedItem(
                item_type=ItemType.paper,
                source="arXiv",
                source_url=source_url,
                canonical_url=canonical,
                external_id=_arxiv_external_id(entry_id),
                title=title,
                published_at_utc=published,
                summary_text=summary,
                content_text=summary,
                tags=tags,
                source_reliability="High",
                timestamp_precision=TimestampPrecision.exact,
                timestamp_confidence=TimestampConfidence.high,
            )
        )
    return out
