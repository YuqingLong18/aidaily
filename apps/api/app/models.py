from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ItemType(str, Enum):
    paper = "paper"
    news = "news"


class Section(str, Enum):
    ai_for_science = "ai_for_science"
    ai_theory_arch = "ai_theory_arch"
    ai_education = "ai_education"
    product_tech = "product_tech"
    market_policy = "market_policy"


class TimestampPrecision(str, Enum):
    exact = "exact"
    date_only = "date_only"


class TimestampConfidence(str, Enum):
    high = "high"
    low = "low"


class Item(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    item_type: ItemType = Field(index=True)
    section: Section = Field(index=True)

    title: str
    source: str = Field(index=True)
    source_url: str = Field(index=True, unique=True)
    canonical_url: Optional[str] = Field(default=None, index=True)
    external_id: Optional[str] = Field(default=None, index=True)

    published_at_utc: datetime = Field(index=True)
    edition_date_local: str = Field(index=True)
    edition_timezone: str = Field(index=True)

    tags_csv: str = Field(default="")
    difficulty: Optional[str] = Field(default=None)

    summary_bullets_md: str = Field(default="")
    why_it_matters_md: str = Field(default="")
    market_impact_md: str = Field(default="")

    source_reliability: Optional[str] = Field(default=None)
    timestamp_precision: TimestampPrecision = Field(default=TimestampPrecision.exact)
    timestamp_confidence: TimestampConfidence = Field(default=TimestampConfidence.high)

    rank_score: float = Field(default=0.0, index=True)

    created_at_utc: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at_utc: datetime = Field(default_factory=lambda: datetime.utcnow())
