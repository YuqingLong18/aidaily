import type { Section } from "./api";

export type Lang = "zh" | "en";

export function sectionLabel(section: Section, lang: Lang = "en"): string {
  switch (section) {
    case "ai_for_science":
      return lang === "zh" ? "科学中的 AI（Top 5）" : "AI for Science (Top 5)";
    case "ai_theory_arch":
      return lang === "zh" ? "AI 理论与架构（Top 5）" : "AI Theory & Architectures (Top 5)";
    case "ai_education":
      return lang === "zh" ? "教育中的 AI（Top 5）" : "AI in Education (Top 5)";
    case "product_tech":
      return lang === "zh" ? "产品与技术观察（Top 3–6）" : "Product & Technology Watch (Top 3–6)";
    case "market_policy":
      return lang === "zh" ? "市场与政策视角（Top 3–5）" : "Market & Policy Lens (Top 3–5)";
  }
}

export function hubLabel(section: Section): "Academic" | "Industry" {
  if (section === "product_tech" || section === "market_policy") return "Industry";
  return "Academic";
}

export const ACADEMIC_SECTIONS: Section[] = ["ai_for_science", "ai_theory_arch", "ai_education"];
export const INDUSTRY_SECTIONS: Section[] = ["product_tech", "market_policy"];
