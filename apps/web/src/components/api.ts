export type Section =
  | "ai_for_science"
  | "ai_theory_arch"
  | "ai_education"
  | "product_tech"
  | "market_policy";

export type ItemType = "paper" | "news";

export type ItemOut = {
  id: string;
  item_type: ItemType;
  section: Section;
  title: string;
  source: string;
  source_url: string;
  canonical_url?: string | null;
  published_at_utc: string;
  edition_date_local: string;
  edition_timezone: string;
  tags: string[];
  difficulty?: string | null;
  summary_bullets: string[];
  why_it_matters?: string | null;
  market_impact?: string | null;
  source_reliability?: string | null;
  rank_score: number;
};

export type EditionMetaOut = {
  edition_date_local: string;
  edition_timezone: string;
  utc_date: string;
  utc_start: string;
  utc_end: string;
  item_count: number;
};

export type EditionOut = {
  edition_date_local: string;
  edition_timezone: string;
  utc_date: string;
  utc_start: string;
  utc_end: string;
  sections: Record<Section, ItemOut[]>;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function fetchEditions(tz: string): Promise<EditionMetaOut[]> {
  const res = await fetch(`${API_BASE}/api/editions?tz=${encodeURIComponent(tz)}&days=7`, {
    cache: "no-store"
  });
  if (!res.ok) throw new Error(`Failed to load editions (${res.status})`);
  return res.json();
}

export async function fetchEdition(tz: string, editionDateLocal: string): Promise<EditionOut> {
  const res = await fetch(
    `${API_BASE}/api/editions/${encodeURIComponent(editionDateLocal)}?tz=${encodeURIComponent(tz)}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(`Failed to load edition (${res.status})`);
  return res.json();
}
