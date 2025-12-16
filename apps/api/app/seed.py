from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List
from uuid import UUID

from app.models import Item, ItemType, Section, TimestampConfidence, TimestampPrecision
from app.time_semantics import EditionWindow


@dataclass(frozen=True)
class SeedItem:
    item_type: ItemType
    section: Section
    title: str
    source: str
    source_url: str
    canonical_url: str | None
    published_at_utc: datetime
    tags: list[str]
    difficulty: str | None
    summary_bullets: list[str]
    why_it_matters: str | None
    market_impact: str | None
    source_reliability: str | None
    timestamp_precision: TimestampPrecision
    timestamp_confidence: TimestampConfidence
    rank_score: float


def _uuid_from_url(url: str) -> UUID:
    from uuid import UUID

    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return UUID(h)


def seed_items_for_window(window: EditionWindow) -> List[SeedItem]:
    d = window.utc_date.isoformat()
    z = timezone.utc
    noon = datetime(window.utc_date.year, window.utc_date.month, window.utc_date.day, 12, 0, 0, tzinfo=z)
    t10 = datetime(window.utc_date.year, window.utc_date.month, window.utc_date.day, 10, 0, 0, tzinfo=z)
    t14 = datetime(window.utc_date.year, window.utc_date.month, window.utc_date.day, 14, 0, 0, tzinfo=z)
    t18 = datetime(window.utc_date.year, window.utc_date.month, window.utc_date.day, 18, 0, 0, tzinfo=z)

    return [
        SeedItem(
            item_type=ItemType.paper,
            section=Section.ai_for_science,
            title=f"Graph-augmented diffusion for protein design (UTC {d})",
            source="arXiv",
            source_url=f"https://arxiv.org/abs/seed-aifs-{d}",
            canonical_url=f"https://arxiv.org/abs/seed-aifs-{d}",
            published_at_utc=t14,
            tags=["AIFS", "diffusion", "biology"],
            difficulty="Advanced",
            summary_bullets=[
                "Combines diffusion models with graph priors to improve structural validity.",
                "Uses constrained decoding to preserve biochemical motifs.",
                "Reports higher success rate on in-silico stability screens.",
            ],
            why_it_matters="Brings generative modeling closer to practical wet-lab iteration loops.",
            market_impact=None,
            source_reliability="High",
            timestamp_precision=TimestampPrecision.exact,
            timestamp_confidence=TimestampConfidence.high,
            rank_score=0.92,
        ),
        SeedItem(
            item_type=ItemType.paper,
            section=Section.ai_theory_arch,
            title=f"Attention sparsity schedules for long-context stability (UTC {d})",
            source="arXiv",
            source_url=f"https://arxiv.org/abs/seed-theory-{d}",
            canonical_url=f"https://arxiv.org/abs/seed-theory-{d}",
            published_at_utc=t10,
            tags=["transformers", "long-context", "optimization"],
            difficulty="Intermediate",
            summary_bullets=[
                "Introduces a training-time sparsity schedule that ramps attention density.",
                "Stabilizes loss spikes when scaling context length.",
                "Maintains perplexity while reducing compute at inference.",
            ],
            why_it_matters="A practical knob for scaling context without retraining from scratch.",
            market_impact=None,
            source_reliability="High",
            timestamp_precision=TimestampPrecision.exact,
            timestamp_confidence=TimestampConfidence.high,
            rank_score=0.88,
        ),
        SeedItem(
            item_type=ItemType.paper,
            section=Section.ai_education,
            title=f"Rubric-aligned feedback agents for classroom writing (UTC {d})",
            source="arXiv",
            source_url=f"https://arxiv.org/abs/seed-edu-{d}",
            canonical_url=f"https://arxiv.org/abs/seed-edu-{d}",
            published_at_utc=noon,
            tags=["education", "feedback", "rubrics"],
            difficulty="Beginner",
            summary_bullets=[
                "Maps rubric criteria to controllable feedback templates.",
                "Reduces harmful over-editing via constraint prompts.",
                "Shows improved student revision outcomes in a small study.",
            ],
            why_it_matters="A clear pathway for safer, pedagogy-aligned classroom use.",
            market_impact=None,
            source_reliability="Medium",
            timestamp_precision=TimestampPrecision.date_only,
            timestamp_confidence=TimestampConfidence.high,
            rank_score=0.77,
        ),
        SeedItem(
            item_type=ItemType.news,
            section=Section.product_tech,
            title=f"Tooling update: evaluation harness adds regression gates (UTC {d})",
            source="Company Blog",
            source_url=f"https://example.com/blog/seed-product-{d}",
            canonical_url=f"https://example.com/blog/seed-product-{d}",
            published_at_utc=t18,
            tags=["product", "evals", "release"],
            difficulty=None,
            summary_bullets=[
                "Adds dataset versioning and score deltas as CI checks.",
                "Introduces per-slice metrics for safety and style.",
                "Publishes a reference pipeline for reproducible runs.",
            ],
            why_it_matters=None,
            market_impact="Makes it easier for teams to prevent silent model regressions in production.",
            source_reliability="High",
            timestamp_precision=TimestampPrecision.exact,
            timestamp_confidence=TimestampConfidence.high,
            rank_score=0.84,
        ),
        SeedItem(
            item_type=ItemType.news,
            section=Section.market_policy,
            title=f"Policy watch: draft guidance on AI transparency reporting (UTC {d})",
            source="Regulator",
            source_url=f"https://example.com/policy/seed-market-{d}",
            canonical_url=f"https://example.com/policy/seed-market-{d}",
            published_at_utc=t10,
            tags=["policy", "transparency"],
            difficulty=None,
            summary_bullets=[
                "Proposes standardized disclosure for training data categories.",
                "Introduces audit-ready documentation expectations for deployments.",
                "Seeks public consultation on enforcement timelines.",
            ],
            why_it_matters=None,
            market_impact="Could raise compliance overhead while improving trust for high-impact deployments.",
            source_reliability="High",
            timestamp_precision=TimestampPrecision.exact,
            timestamp_confidence=TimestampConfidence.high,
            rank_score=0.8,
        ),
    ]


def to_model(seed: SeedItem, window: EditionWindow) -> Item:
    summary_md = "\n".join([f"- {b}" for b in seed.summary_bullets])
    return Item(
        id=_uuid_from_url(seed.source_url),
        item_type=seed.item_type,
        section=seed.section,
        title=seed.title,
        source=seed.source,
        source_url=seed.source_url,
        canonical_url=seed.canonical_url,
        published_at_utc=seed.published_at_utc.astimezone(timezone.utc),
        edition_date_local=window.edition_date_local.isoformat(),
        edition_timezone=window.edition_timezone,
        tags_csv=",".join(seed.tags),
        difficulty=seed.difficulty,
        summary_bullets_md=summary_md,
        why_it_matters_md=seed.why_it_matters or "",
        market_impact_md=seed.market_impact or "",
        source_reliability=seed.source_reliability,
        timestamp_precision=seed.timestamp_precision,
        timestamp_confidence=seed.timestamp_confidence,
        rank_score=seed.rank_score,
    )
