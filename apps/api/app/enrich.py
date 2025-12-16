from __future__ import annotations

from dataclasses import replace

from app.ingestion_types import RawIngestedItem
from app.models import ItemType, TimestampConfidence
from app.scrape import scrape_article_text


def enrich_with_scraping(
    items: list[RawIngestedItem],
    *,
    scrape_news: bool,
    max_news_to_scrape: int = 40,
) -> list[RawIngestedItem]:
    if not scrape_news:
        return items

    out: list[RawIngestedItem] = []
    scraped = 0
    for item in items:
        if item.item_type != ItemType.news or scraped >= max_news_to_scrape:
            out.append(item)
            continue

        try:
            text = scrape_article_text(item.source_url)
            if text:
                out.append(replace(item, content_text=text))
            else:
                out.append(item)
        except Exception:  # noqa: BLE001
            # Network/parsing failures are common; degrade confidence and move on.
            out.append(replace(item, timestamp_confidence=TimestampConfidence.low))
        scraped += 1
    return out

