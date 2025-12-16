from __future__ import annotations

import json
from typing import Any, Iterable

from app.openrouter_client import chat_json, load_openrouter_config
from app.translation_prompt import system_prompt, user_prompt


def _chunks(seq: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def translate_items_to_zh(items: list[Any], *, batch_size: int = 18) -> dict[str, dict[str, Any]]:
    """
    Returns mapping: item_id -> translated fields (zh).
    Expects items to have: id, title, tags[], summary_bullets[], why_it_matters, market_impact.
    """
    cfg = load_openrouter_config()
    out: dict[str, dict[str, Any]] = {}

    for chunk in _chunks(items, batch_size):
        items_json = json.dumps(chunk, ensure_ascii=False)
        payload = chat_json(system=system_prompt(), user=user_prompt(items_json), config=cfg)
        for obj in payload.get("items") or []:
            item_id = str(obj.get("id") or "")
            if not item_id:
                continue
            out[item_id] = {
                "title_zh": obj.get("title_zh"),
                "tags_zh": obj.get("tags_zh") or [],
                "summary_bullets_zh": obj.get("summary_bullets_zh") or [],
                "why_it_matters_zh": obj.get("why_it_matters_zh"),
                "market_impact_zh": obj.get("market_impact_zh"),
            }
    return out

