from __future__ import annotations

from app.models import ItemType, Section


def section_display(section: Section) -> str:
    mapping = {
        Section.ai_for_science: "AI for Science",
        Section.ai_theory_arch: "AI Theory & Architectures",
        Section.ai_education: "AI in Education",
        Section.product_tech: "Product & Technology Watch",
        Section.market_policy: "Market & Policy Lens",
    }
    return mapping.get(section, str(section))


def system_prompt() -> str:
    return "\n".join(
        [
            "You are the editor for a daily AI intelligence dashboard.",
            "You must return STRICT JSON that matches the requested schema. No markdown, no extra keys.",
            "Be factual and conservative: do not invent details beyond the provided text snippet.",
            "If info is missing/uncertain, keep bullets generic and set timestamp_confidence='low'.",
            "Keep output concise and skimmable.",
        ]
    )


def user_prompt(
    *,
    section: Section,
    top_k: int,
    items_json: str,
) -> str:
    sec = section_display(section)
    return f"""
Section: {sec}

Goal: pick the top {top_k} items for this section and enrich ALL provided items with:
- tags (2-6 short keywords)
- summary_bullets (papers: 3-5, news: 2-4)
- why_it_matters (papers only; 1 sentence)
- market_impact (news only; 1 sentence)
- difficulty (papers only; one of: Beginner, Intermediate, Advanced; else null)
- source_reliability (High/Medium/Low based only on source reputation signals in snippet; default Medium)
- importance_score (0-100; higher = more impactful for readers today)
- timestamp_confidence (high/low; if snippet lacks clear time cues or seems ambiguous, use low)

Return JSON in exactly this shape:
{{
  "section": "{section.value}",
  "top_ids": ["<id>", "..."],
  "items": [
    {{
      "id": "<id>",
      "tags": ["...", "..."],
      "summary_bullets": ["...", "..."],
      "why_it_matters": "..." | null,
      "market_impact": "..." | null,
      "difficulty": "Beginner" | "Intermediate" | "Advanced" | null,
      "source_reliability": "High" | "Medium" | "Low",
      "importance_score": 0,
      "timestamp_confidence": "high" | "low"
    }}
  ]
}}

Items (JSON array):
{items_json}
""".strip()


def item_payload(
    *,
    id: str,
    item_type: ItemType,
    title: str,
    source: str,
    source_url: str,
    published_at_utc_iso: str,
    snippet: str,
) -> dict:
    snippet = (snippet or "").strip()
    if len(snippet) > 1800:
        snippet = snippet[:1800] + "…"
    return {
        "id": id,
        "type": item_type.value,
        "title": title,
        "source": source,
        "url": source_url,
        "published_at_utc": published_at_utc_iso,
        "snippet": snippet,
    }

