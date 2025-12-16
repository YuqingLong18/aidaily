from __future__ import annotations

import argparse
from datetime import date

from app.db import init_db, session_scope
from app.repo import upsert_by_source_url
from app.seed import seed_items_for_window, to_model
from app.time_semantics import edition_window_for_local_date, local_today


def ingest(edition_date_local: date, tz: str) -> int:
    init_db()
    window = edition_window_for_local_date(edition_date_local, tz)
    seeded = seed_items_for_window(window)

    written = 0
    with session_scope() as session:
        for s in seeded:
            model = to_model(s, window)
            upsert_by_source_url(session, model)
            written += 1
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexus AI Daily ingestion (MVP seed)")
    parser.add_argument("--tz", default="Asia/Hong_Kong")
    parser.add_argument("--date", dest="edition_date_local", default=None, help="Local edition date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=1, help="Number of local edition days to seed (default: 1)")
    args = parser.parse_args()

    tz = args.tz
    if args.edition_date_local is None:
        d = local_today(tz)
    else:
        d = date.fromisoformat(args.edition_date_local)

    if args.days < 1 or args.days > 31:
        raise SystemExit("--days must be between 1 and 31")

    total = 0
    for i in range(args.days):
        day = d.fromordinal(d.toordinal() - i)
        total += ingest(day, tz)
    print(f"seeded {total} items across {args.days} edition day(s) ending {d.isoformat()} ({tz})")


if __name__ == "__main__":
    main()
