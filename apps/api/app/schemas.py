from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import ItemType, Section, TimestampConfidence, TimestampPrecision


class ItemOut(BaseModel):
    id: UUID
    item_type: ItemType
    section: Section
    title: str
    title_zh: Optional[str] = None
    source: str
    source_url: str
    canonical_url: Optional[str] = None
    published_at_utc: datetime
    edition_date_local: str
    edition_timezone: str
    tags: List[str] = Field(default_factory=list)
    tags_zh: List[str] = Field(default_factory=list)
    difficulty: Optional[str] = None
    summary_bullets: List[str] = Field(default_factory=list)
    summary_bullets_zh: List[str] = Field(default_factory=list)
    why_it_matters: Optional[str] = None
    why_it_matters_zh: Optional[str] = None
    market_impact: Optional[str] = None
    market_impact_zh: Optional[str] = None
    source_reliability: Optional[str] = None
    timestamp_precision: TimestampPrecision
    timestamp_confidence: TimestampConfidence
    rank_score: float


class EditionMetaOut(BaseModel):
    edition_date_local: str
    edition_timezone: str
    utc_date: str
    utc_start: datetime
    utc_end: datetime
    item_count: int


class EditionOut(BaseModel):
    edition_date_local: str
    edition_timezone: str
    utc_date: str
    utc_start: datetime
    utc_end: datetime
    sections: dict[Section, List[ItemOut]]
