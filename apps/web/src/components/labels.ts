import type { Section } from "./api";

export function sectionLabel(section: Section): string {
  switch (section) {
    case "ai_for_science":
      return "AI for Science (Top 5)";
    case "ai_theory_arch":
      return "AI Theory & Architectures (Top 5)";
    case "ai_education":
      return "AI in Education (Top 5)";
    case "product_tech":
      return "Product & Technology Watch (Top 3–6)";
    case "market_policy":
      return "Market & Policy Lens (Top 3–5)";
  }
}

export function hubLabel(section: Section): "Academic" | "Industry" {
  if (section === "product_tech" || section === "market_policy") return "Industry";
  return "Academic";
}

export const ACADEMIC_SECTIONS: Section[] = ["ai_for_science", "ai_theory_arch", "ai_education"];
export const INDUSTRY_SECTIONS: Section[] = ["product_tech", "market_policy"];
