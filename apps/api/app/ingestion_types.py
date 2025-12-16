from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.models import ItemType, TimestampConfidence, TimestampPrecision


@dataclass(frozen=True)
class RawIngestedItem:
    item_type: ItemType
    source: str
    source_url: str
    canonical_url: Optional[str]
    external_id: Optional[str]
    title: str
    published_at_utc: datetime
    summary_text: str
    content_text: Optional[str]
    tags: list[str]
    source_reliability: Optional[str]
    timestamp_precision: TimestampPrecision
    timestamp_confidence: TimestampConfidence

