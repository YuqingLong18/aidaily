from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class EditionWindow:
    edition_date_local: date
    edition_timezone: str
    utc_date: date
    utc_start: datetime
    utc_end: datetime


def local_today(tz: str) -> date:
    return datetime.now(ZoneInfo(tz)).date()


def edition_window_for_local_date(edition_date_local: date, tz: str) -> EditionWindow:
    utc_date = edition_date_local - timedelta(days=1)
    utc_start = datetime.combine(utc_date, time(0, 0, 0), tzinfo=timezone.utc)
    utc_end = datetime.combine(utc_date, time(23, 59, 59), tzinfo=timezone.utc)
    return EditionWindow(
        edition_date_local=edition_date_local,
        edition_timezone=tz,
        utc_date=utc_date,
        utc_start=utc_start,
        utc_end=utc_end,
    )
