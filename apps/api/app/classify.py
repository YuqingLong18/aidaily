from __future__ import annotations

from app.models import ItemType, Section


def classify_section(item_type: ItemType, text: str) -> Section:
    t = (text or "").lower()

    if item_type == ItemType.paper:
        if any(k in t for k in ["protein", "molecule", "drug", "chemistry", "biology", "genomics", "materials", "crystal", "weather", "climate"]):
            return Section.ai_for_science
        if any(k in t for k in ["education", "classroom", "student", "teacher", "curriculum", "tutor", "learning outcome", "assessment", "rubric"]):
            return Section.ai_education
        return Section.ai_theory_arch

    if any(k in t for k in ["policy", "regulat", "law", "ban", "compliance", "election", "senate", "parliament", "antitrust", "investigation"]):
        return Section.market_policy
    if any(k in t for k in ["funding", "ipo", "acquisition", "merger", "valuation", "lawsuit", "fine"]):
        return Section.market_policy
    return Section.product_tech

