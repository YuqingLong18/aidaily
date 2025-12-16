from __future__ import annotations


def system_prompt() -> str:
    return "\n".join(
        [
            "You are a professional technical translator.",
            "Translate English to Simplified Chinese for an AI news dashboard.",
            "Return STRICT JSON only (no markdown, no extra keys).",
            "Preserve URLs, numbers, dates, and code tokens as-is.",
            "Keep company/product/model names in English; if helpful, add a short Chinese descriptor after it.",
            "Keep tags short (2-6 words each).",
            "Do not add new facts.",
        ]
    )


def user_prompt(items_json: str) -> str:
    return f"""
Translate these items to Simplified Chinese.

Return JSON with exactly this shape:
{{
  "items": [
    {{
      "id": "<id>",
      "title_zh": "<zh>",
      "tags_zh": ["...", "..."],
      "summary_bullets_zh": ["...", "..."],
      "why_it_matters_zh": "..." | null,
      "market_impact_zh": "..." | null
    }}
  ]
}}

Items (JSON array):
{items_json}
""".strip()

