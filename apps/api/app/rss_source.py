from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

import feedparser

from app.http_client import fetch_text
from app.ingestion_types import RawIngestedItem
from app.models import ItemType, TimestampConfidence, TimestampPrecision
from app.time_semantics import EditionWindow
from app.url_utils import canonicalize_url


def _published_dt_utc(entry: dict) -> Optional[datetime]:
    if "published" in entry and entry["published"]:
        try:
            dt = parsedate_to_datetime(entry["published"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:  # noqa: BLE001
            pass

    if "updated" in entry and entry["updated"]:
        try:
            dt = parsedate_to_datetime(entry["updated"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:  # noqa: BLE001
            pass

    return None


def _entry_text(entry: dict) -> str:
    summary = (entry.get("summary") or "").strip()
    if summary:
        return summary
    content = entry.get("content") or []
    if content and isinstance(content, list) and isinstance(content[0], dict):
        return (content[0].get("value") or "").strip()
    return ""


def fetch_rss_items(
    window: EditionWindow,
    *,
    feed_url: str,
    source_name: str,
    item_type: ItemType = ItemType.news,
    max_items: int = 100,
    reliability: Optional[str] = None,
) -> list[RawIngestedItem]:
    parsed = feedparser.parse(fetch_text(feed_url))
    out: List[RawIngestedItem] = []

    for entry in parsed.entries[:max_items]:
        title = " ".join((entry.get("title") or "").split())
        link = entry.get("link") or ""
        if not title or not link:
            continue

        published = _published_dt_utc(entry)
        if published is None:
            continue

        if published < window.utc_start or published > window.utc_end:
            continue

        source_url = canonicalize_url(link)
        canonical = source_url

        tags = []
        for t in entry.get("tags") or []:
            term = (t.get("term") or "").strip()
            if term:
                tags.append(term)

        text = _entry_text(entry)
        out.append(
            RawIngestedItem(
                item_type=item_type,
                source=source_name,
                source_url=source_url,
                canonical_url=canonical,
                external_id=None,
                title=title,
                published_at_utc=published,
                summary_text=text,
                content_text=None,
                tags=tags,
                source_reliability=reliability,
                timestamp_precision=TimestampPrecision.exact,
                timestamp_confidence=TimestampConfidence.high,
            )
        )

    return out

