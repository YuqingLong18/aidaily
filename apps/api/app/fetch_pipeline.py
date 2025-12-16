from __future__ import annotations

import sys
from typing import List

from app.arxiv_source import fetch_arxiv_items
from app.ingestion_types import RawIngestedItem
from app.models import ItemType
from app.rss_source import fetch_rss_items
from app.source_config import SourceConfig
from app.time_semantics import EditionWindow


def fetch_all_sources(window: EditionWindow, *, config: SourceConfig) -> list[RawIngestedItem]:
    out: List[RawIngestedItem] = []

    try:
        out.extend(
            fetch_arxiv_items(
                window,
                categories=config.arxiv_categories,
                max_results=config.arxiv_max_results,
            )
        )
    except Exception as e:  # noqa: BLE001
        print(f"[warn] arXiv fetch failed: {e}", file=sys.stderr)

    for name, url in config.industry_feeds:
        try:
            out.extend(
                fetch_rss_items(
                    window,
                    feed_url=url,
                    source_name=name,
                    item_type=ItemType.news,
                    max_items=config.industry_max_items_per_feed,
                    reliability="Medium",
                )
            )
        except Exception as e:  # noqa: BLE001
            print(f"[warn] feed fetch failed ({name}): {e}", file=sys.stderr)

    return out
