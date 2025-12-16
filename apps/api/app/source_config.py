from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Tuple


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def parse_named_urls(value: str) -> list[tuple[str, str]]:
    """
    Format: `Name|https://example.com/feed.xml,Other|https://...`
    """
    pairs: list[tuple[str, str]] = []
    for raw in _split_csv(value):
        if "|" not in raw:
            continue
        name, url = raw.split("|", 1)
        name = name.strip()
        url = url.strip()
        if name and url:
            pairs.append((name, url))
    return pairs


@dataclass(frozen=True)
class SourceConfig:
    arxiv_categories: List[str]
    arxiv_max_results: int
    industry_feeds: List[Tuple[str, str]]
    industry_max_items_per_feed: int


def load_source_config() -> SourceConfig:
    arxiv_categories = _split_csv(os.getenv("NEXUS_ARXIV_CATEGORIES", "cs.LG,cs.AI,cs.CL,cs.CV,stat.ML"))
    arxiv_max_results = int(os.getenv("NEXUS_ARXIV_MAX_RESULTS", "250"))

    default_industry = ",".join(
        [
            "TechCrunch AI|https://techcrunch.com/tag/artificial-intelligence/feed/",
            "VentureBeat AI|https://venturebeat.com/category/ai/feed/",
            "Hugging Face Blog|https://huggingface.co/blog/feed.xml",
            "GitHub Blog|https://github.blog/feed/",
        ]
    )
    industry_feeds = parse_named_urls(os.getenv("NEXUS_INDUSTRY_FEEDS", default_industry))
    industry_max_items = int(os.getenv("NEXUS_INDUSTRY_MAX_ITEMS_PER_FEED", "80"))

    return SourceConfig(
        arxiv_categories=arxiv_categories,
        arxiv_max_results=arxiv_max_results,
        industry_feeds=industry_feeds,
        industry_max_items_per_feed=industry_max_items,
    )

