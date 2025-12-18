from __future__ import annotations

import argparse
from datetime import date

from app.db import init_db, session_scope
from app.enrich import enrich_with_scraping
from app.fetch_pipeline import fetch_all_sources
from app.normalize import to_item_model
from app.repo import upsert_by_source_url, upsert_item
from app.seed import seed_items_for_window, to_model
from app.source_config import load_source_config
from app.time_semantics import edition_window_for_local_date, local_today


def ingest_seed(edition_date_local: date, tz: str) -> int:
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


def ingest_live(
    edition_date_local: date,
    tz: str,
    *,
    scrape_news: bool,
    max_news_to_scrape: int,
    dry_run: bool,
    print_window: bool,
) -> int:
    window = edition_window_for_local_date(edition_date_local, tz)
    if print_window:
        print(
            f"edition {window.edition_date_local.isoformat()} ({tz}) => UTC {window.utc_date.isoformat()} "
            f"[{window.utc_start.isoformat()} .. {window.utc_end.isoformat()}]"
        )

    config = load_source_config()

    raw = fetch_all_sources(window, config=config)
    raw = enrich_with_scraping(raw, scrape_news=scrape_news, max_news_to_scrape=max_news_to_scrape)

    seen: set[str] = set()
    written = 0
    if dry_run:
        for r in raw:
            if r.source_url in seen:
                continue
            seen.add(r.source_url)
            written += 1
        return written

    init_db()
    with session_scope() as session:
        for r in raw:
            if r.source_url in seen:
                continue
            seen.add(r.source_url)
            model = to_item_model(r, window)
            upsert_item(session, model)
            written += 1
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexus AI Daily ingestion")
    parser.add_argument("--tz", default="Asia/Shanghai")
    parser.add_argument("--date", dest="edition_date_local", default=None, help="Local edition date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=1, help="Number of local edition days to seed (default: 1)")
    parser.add_argument(
        "--dates",
        default=None,
        help="Comma-separated local edition dates (YYYY-MM-DD,YYYY-MM-DD). Overrides --date/--days if set.",
    )
    parser.add_argument("--mode", choices=["live", "seed"], default="live")
    parser.add_argument("--scrape-news", action="store_true", help="Fetch article pages to improve summaries (slower)")
    parser.add_argument("--max-news-to-scrape", type=int, default=35)
    parser.add_argument("--dry-run", action="store_true", help="Fetch + filter, but do not write to DB")
    parser.add_argument("--print-window", action="store_true", help="Print the UTC window for the edition date(s)")
    parser.add_argument("--curate", action="store_true", help="After ingestion, run LLM curation for the edition(s)")
    args = parser.parse_args()

    tz = args.tz
    if args.dates is not None:
        raw_dates = [p.strip() for p in str(args.dates).split(",") if p.strip()]
        if not raw_dates:
            raise SystemExit("--dates cannot be empty")
        try:
            dates = sorted({date.fromisoformat(d) for d in raw_dates}, reverse=True)
        except ValueError as e:
            raise SystemExit("--dates must be YYYY-MM-DD,YYYY-MM-DD,...") from e
    else:
        if args.edition_date_local is None:
            d = local_today(tz)
        else:
            d = date.fromisoformat(args.edition_date_local)

        if args.days < 1 or args.days > 31:
            raise SystemExit("--days must be between 1 and 31")

        dates = [d.fromordinal(d.toordinal() - i) for i in range(args.days)]

    total = 0
    for day in dates:
        if args.mode == "seed":
            total += ingest_seed(day, tz)
        else:
            total += ingest_live(
                day,
                tz,
                scrape_news=bool(args.scrape_news),
                max_news_to_scrape=int(args.max_news_to_scrape),
                dry_run=bool(args.dry_run),
                print_window=bool(args.print_window),
            )
        if args.curate and not args.dry_run:
            from app.curate import curate_edition

            curate_edition(day, tz, dry_run=False)

    label = "seeded" if args.mode == "seed" else "ingested"
    if args.dry_run and args.mode == "live":
        label = "fetched"
    dates_label = ", ".join([d.isoformat() for d in dates])
    print(f"{label} {total} items across {len(dates)} edition day(s): {dates_label} ({tz})")


if __name__ == "__main__":
    main()
