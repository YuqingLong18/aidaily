from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models import Item, Section


def get_item(session: Session, item_id: UUID) -> Optional[Item]:
    return session.get(Item, item_id)


def list_items_for_edition(session: Session, edition_date_local: str, tz: str) -> list[Item]:
    stmt = (
        select(Item)
        .where(Item.edition_date_local == edition_date_local)
        .where(Item.edition_timezone == tz)
        .order_by(Item.rank_score.desc(), Item.published_at_utc.desc())
    )
    return list(session.exec(stmt).all())


def count_items_for_edition(session: Session, edition_date_local: str, tz: str) -> int:
    return len(list_items_for_edition(session, edition_date_local, tz))


def upsert_by_source_url(session: Session, incoming: Item) -> Item:
    existing = session.exec(select(Item).where(Item.source_url == incoming.source_url)).first()
    now = datetime.utcnow()
    if existing is None:
        incoming.created_at_utc = now
        incoming.updated_at_utc = now
        session.add(incoming)
        session.commit()
        session.refresh(incoming)
        return incoming

    for field_name, value in incoming.model_dump(exclude={"id", "created_at_utc"}).items():
        setattr(existing, field_name, value)
    existing.updated_at_utc = now
    session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing


def top_by_section(items: Iterable[Item], limit_by_section: dict[Section, int]) -> dict[Section, list[Item]]:
    grouped: dict[Section, list[Item]] = {s: [] for s in Section}
    for item in items:
        if item.section not in grouped:
            grouped[item.section] = []
        grouped[item.section].append(item)
    for section, limit in limit_by_section.items():
        grouped[section] = grouped.get(section, [])[:limit]
    return grouped
