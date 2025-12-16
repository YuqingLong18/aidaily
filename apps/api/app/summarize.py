from __future__ import annotations

from app.models import ItemType
from app.text_utils import split_sentences, strip_htmlish


def summarize_bullets(item_type: ItemType, title: str, text: str, *, max_bullets: int) -> list[str]:
    clean = strip_htmlish(text)
    sentences = split_sentences(clean)
    if not sentences:
        return []

    bullets: list[str] = []
    for s in sentences:
        if len(s) < 40:
            continue
        bullets.append(s)
        if len(bullets) >= max_bullets:
            break

    if not bullets:
        bullets = sentences[: max_bullets]

    if item_type == ItemType.news and bullets and title:
        if bullets[0].lower().startswith(title.lower()[:24]):
            bullets = bullets[1:] or bullets

    return bullets[:max_bullets]


def why_it_matters_hint(item_type: ItemType, title: str, text: str) -> str | None:
    if item_type != ItemType.paper:
        return None
    t = f"{title}\n{text}".lower()
    if "open source" in t or "code" in t or "github" in t:
        return "Provides an implementable result with released code, making follow-up experimentation faster."
    if "benchmark" in t or "dataset" in t:
        return "Adds a new benchmark signal that can shift evaluation and model selection decisions."
    if "theorem" in t or "proof" in t:
        return "Clarifies a theoretical mechanism that can inform architecture and training choices."
    return "Useful signal for tracking where research effort is moving."


def market_impact_hint(item_type: ItemType, title: str, text: str) -> str | None:
    if item_type != ItemType.news:
        return None
    t = f"{title}\n{text}".lower()
    if any(k in t for k in ["regulat", "policy", "law", "ban", "compliance"]):
        return "Likely impacts compliance expectations and deployment timelines for AI products."
    if any(k in t for k in ["funding", "acquisition", "valuation", "ipo"]):
        return "Signals capital allocation and competitive pressure in the AI ecosystem."
    if any(k in t for k in ["launch", "release", "product", "api", "model"]):
        return "May shift the baseline for features or pricing in AI tooling and platforms."
    return "Potentially relevant for product strategy and competitive monitoring."

