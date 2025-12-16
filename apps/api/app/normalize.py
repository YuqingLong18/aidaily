from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from uuid import UUID

from app.classify import classify_section
from app.ingestion_types import RawIngestedItem
from app.models import Item, ItemType, TimestampConfidence, TimestampPrecision
from app.summarize import market_impact_hint, summarize_bullets, why_it_matters_hint
from app.text_utils import strip_htmlish
from app.time_semantics import EditionWindow
from app.url_utils import canonicalize_url


def _uuid_from_dedup_key(key: str) -> UUID:
    from uuid import UUID

    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    return UUID(h)


def _difficulty_hint(text: str) -> str | None:
    t = (text or "").lower()
    if any(k in t for k in ["theorem", "proof", "convergence", "optimality", "complexity bound"]):
        return "Advanced"
    if any(k in t for k in ["ablation", "benchmark", "dataset", "experiment"]):
        return "Intermediate"
    return None


def _reliability_weight(label: str | None) -> float:
    if not label:
        return 0.5
    l = label.lower()
    if l == "high":
        return 1.0
    if l == "medium":
        return 0.7
    if l == "low":
        return 0.4
    return 0.5


def _rank_score(published_at_utc: datetime, window: EditionWindow, reliability: str | None) -> float:
    span = (window.utc_end - window.utc_start).total_seconds() or 1.0
    pos = (published_at_utc - window.utc_start).total_seconds()
    recency = min(max(pos / span, 0.0), 1.0)
    return round(0.65 * recency + 0.35 * _reliability_weight(reliability), 4)


def to_item_model(raw: RawIngestedItem, window: EditionWindow) -> Item:
    title = raw.title.strip()
    source_url = canonicalize_url(raw.source_url)
    canonical_url = canonicalize_url(raw.canonical_url) if raw.canonical_url else None

    combined_text = "\n".join([title, raw.summary_text or "", raw.content_text or ""])
    section = classify_section(raw.item_type, combined_text)

    if raw.item_type == ItemType.paper:
        bullets = summarize_bullets(ItemType.paper, title, raw.summary_text or raw.content_text or "", max_bullets=5)
    else:
        bullets = summarize_bullets(ItemType.news, title, raw.content_text or raw.summary_text or "", max_bullets=4)

    summary_md = "\n".join([f"- {b}" for b in bullets])

    why = why_it_matters_hint(raw.item_type, title, raw.summary_text or raw.content_text or "")
    market = market_impact_hint(raw.item_type, title, raw.content_text or raw.summary_text or "")

    cleaned_tags = []
    for t in raw.tags:
        t = strip_htmlish(t).strip()
        if not t:
            continue
        if t not in cleaned_tags:
            cleaned_tags.append(t)

    dedup_key = source_url or canonical_url or f"{raw.source}:{raw.external_id or ''}:{title}:{raw.published_at_utc.isoformat()}"

    return Item(
        id=_uuid_from_dedup_key(dedup_key),
        item_type=raw.item_type,
        section=section,
        title=title,
        source=raw.source,
        source_url=source_url,
        canonical_url=canonical_url,
        external_id=raw.external_id,
        published_at_utc=raw.published_at_utc.astimezone(timezone.utc),
        edition_date_local=window.edition_date_local.isoformat(),
        edition_timezone=window.edition_timezone,
        tags_csv=",".join(cleaned_tags),
        difficulty=_difficulty_hint(combined_text) if raw.item_type == ItemType.paper else None,
        summary_bullets_md=summary_md,
        why_it_matters_md=why or "",
        market_impact_md=market or "",
        source_reliability=raw.source_reliability,
        timestamp_precision=raw.timestamp_precision if isinstance(raw.timestamp_precision, TimestampPrecision) else TimestampPrecision.exact,
        timestamp_confidence=raw.timestamp_confidence if isinstance(raw.timestamp_confidence, TimestampConfidence) else TimestampConfidence.high,
        rank_score=_rank_score(raw.published_at_utc, window, raw.source_reliability),
    )

