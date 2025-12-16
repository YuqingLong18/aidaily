from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import Any

from app.curation_prompt import item_payload, system_prompt, user_prompt
from app.db import init_db, session_scope
from app.models import ItemType, Section, TimestampConfidence
from app.openrouter_client import chat_json, load_openrouter_config
from app.repo import list_items_for_edition
from app.time_semantics import local_today
from app.translate import translate_items_to_zh


def _limit_by_section() -> dict[Section, int]:
    return {
        Section.ai_for_science: 5,
        Section.ai_theory_arch: 5,
        Section.ai_education: 5,
        Section.product_tech: 6,
        Section.market_policy: 5,
    }


def _candidate_limit(section: Section) -> int:
    if section in {Section.product_tech, Section.market_policy}:
        return 22
    return 24


def _item_snippet(item) -> str:
    if item.item_type == ItemType.paper:
        return item.summary_bullets_md or ""
    if item.market_impact_md:
        return item.market_impact_md
    if item.summary_bullets_md:
        return item.summary_bullets_md
    return ""


def _apply_curation(section: Section, payload: dict[str, Any], items_by_id: dict[str, Any]) -> tuple[int, list[str]]:
    updated = 0
    top_ids = [str(x) for x in (payload.get("top_ids") or []) if x]
    top_bonus: dict[str, float] = {}
    for idx, tid in enumerate(top_ids):
        top_bonus[tid] = max(0.7, 1.0 - (idx * 0.03))

    for obj in payload.get("items") or []:
        item_id = str(obj.get("id") or "")
        if not item_id or item_id not in items_by_id:
            continue

        item = items_by_id[item_id]
        tags = obj.get("tags") or []
        bullets = obj.get("summary_bullets") or []

        item.tags_csv = ",".join([t.strip() for t in tags if isinstance(t, str) and t.strip()][:8])
        item.summary_bullets_md = "\n".join([f"- {b.strip()}" for b in bullets if isinstance(b, str) and b.strip()])

        why = obj.get("why_it_matters")
        market = obj.get("market_impact")
        item.why_it_matters_md = (why or "") if isinstance(why, str) else ""
        item.market_impact_md = (market or "") if isinstance(market, str) else ""

        diff = obj.get("difficulty")
        item.difficulty = diff if diff in {"Beginner", "Intermediate", "Advanced"} else None

        rel = obj.get("source_reliability")
        item.source_reliability = rel if rel in {"High", "Medium", "Low"} else (item.source_reliability or "Medium")

        score = obj.get("importance_score")
        try:
            score_f = float(score)
        except Exception:  # noqa: BLE001
            score_f = 0.0
        score_f = max(0.0, min(100.0, score_f))
        item.rank_score = round(score_f / 100.0, 4)
        if item_id in top_bonus:
            item.rank_score = round(max(item.rank_score, top_bonus[item_id]), 4)

        tc = obj.get("timestamp_confidence")
        item.timestamp_confidence = TimestampConfidence.low if tc == "low" else TimestampConfidence.high

        if item.section != section:
            item.section = section

        updated += 1

    return updated, top_ids


def curate_edition(edition_date_local: date, tz: str, *, dry_run: bool) -> None:
    init_db()
    with session_scope() as session:
        items = list_items_for_edition(session, edition_date_local.isoformat(), tz)
        items_by_id = {str(i.id): i for i in items}

        by_section: dict[Section, list[Any]] = {s: [] for s in Section}
        for i in items:
            by_section[i.section].append(i)

        limits = _limit_by_section()
        total_updated = 0
        total_top = 0

        cfg = load_openrouter_config()
        print(f"curating {edition_date_local.isoformat()} ({tz}) with model {cfg.model}")

        for section in Section:
            candidates = sorted(by_section.get(section, []), key=lambda x: x.published_at_utc, reverse=True)[: _candidate_limit(section)]
            if not candidates:
                continue

            items_json = json.dumps(
                [
                    item_payload(
                        id=str(i.id),
                        item_type=i.item_type,
                        title=i.title,
                        source=i.source,
                        source_url=i.source_url,
                        published_at_utc_iso=i.published_at_utc.isoformat(),
                        snippet=_item_snippet(i),
                    )
                    for i in candidates
                ],
                ensure_ascii=False,
            )

            payload = chat_json(
                system=system_prompt(),
                user=user_prompt(section=section, top_k=limits[section], items_json=items_json),
                config=cfg,
            )

            updated, top_ids = _apply_curation(section, payload, items_by_id)
            total_updated += updated
            total_top += len(top_ids)

            prefix = "[dry-run] " if dry_run else ""
            print(f"{prefix}{section.value}: updated {updated}, top {len(top_ids)}")

        if not dry_run:
            session.commit()

            # Translation pass (English -> Simplified Chinese) for UI toggle.
            trans_in = []
            for i in items:
                trans_in.append(
                    {
                        "id": str(i.id),
                        "title": i.title,
                        "tags": [t.strip() for t in (i.tags_csv or "").split(",") if t.strip()],
                        "summary_bullets": [
                            b.strip("- ").strip() for b in (i.summary_bullets_md or "").splitlines() if b.strip()
                        ],
                        "why_it_matters": i.why_it_matters_md or None,
                        "market_impact": i.market_impact_md or None,
                    }
                )

            translated = translate_items_to_zh(trans_in)
            for item_id, fields in translated.items():
                it = items_by_id.get(item_id)
                if not it:
                    continue
                title_zh = fields.get("title_zh")
                if isinstance(title_zh, str) and title_zh.strip():
                    it.title_zh = title_zh.strip()

                tags_zh = fields.get("tags_zh") or []
                it.tags_zh_csv = ",".join([t.strip() for t in tags_zh if isinstance(t, str) and t.strip()][:8])

                bullets_zh = fields.get("summary_bullets_zh") or []
                it.summary_bullets_zh_md = "\n".join(
                    [f"- {b.strip()}" for b in bullets_zh if isinstance(b, str) and b.strip()]
                )

                w = fields.get("why_it_matters_zh")
                it.why_it_matters_zh_md = w.strip() if isinstance(w, str) and w.strip() else ""
                m = fields.get("market_impact_zh")
                it.market_impact_zh_md = m.strip() if isinstance(m, str) and m.strip() else ""

            session.commit()
            print("translation: updated zh fields")

        print(f"done: updated {total_updated} item(s), top picks declared {total_top} (ids only)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Curate an edition via OpenRouter LLM")
    parser.add_argument("--tz", default="Asia/Shanghai")
    parser.add_argument("--date", dest="edition_date_local", default=None, help="Local edition date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.edition_date_local is None:
        d = local_today(args.tz)
    else:
        d = date.fromisoformat(args.edition_date_local)

    try:
        curate_edition(d, args.tz, dry_run=bool(args.dry_run))
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
