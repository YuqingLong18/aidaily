"use client";

import { useEffect, useMemo, useState } from "react";
import type { EditionMetaOut, EditionOut, ItemOut, Section } from "./api";
import { fetchEdition, fetchEditions } from "./api";
import { ACADEMIC_SECTIONS, INDUSTRY_SECTIONS, sectionLabel } from "./labels";

const TZ_PRESETS = ["Asia/Hong_Kong", "UTC", "America/Los_Angeles", "Europe/London", "Asia/Tokyo"];
const ALL_SECTIONS: Section[] = [...ACADEMIC_SECTIONS, ...INDUSTRY_SECTIONS];

function prettyLocalLabel(isoDate: string): string {
  const [, m, d] = isoDate.split("-").map(Number);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${String(d).padStart(2, "0")} ${months[m - 1] ?? ""}`;
}

function prettyUtc(publishedAtUtc: string): string {
  const dt = new Date(publishedAtUtc);
  if (Number.isNaN(dt.getTime())) return publishedAtUtc;
  const m = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][dt.getUTCMonth()] ?? "";
  const d = String(dt.getUTCDate()).padStart(2, "0");
  const hh = String(dt.getUTCHours()).padStart(2, "0");
  const mm = String(dt.getUTCMinutes()).padStart(2, "0");
  return `${d} ${m} ${hh}:${mm} UTC`;
}

function cardWhyLabel(item: ItemOut): string {
  if (item.item_type === "paper") return "Why it matters:";
  return "Market/impact:";
}

function cardWhyText(item: ItemOut): string | null {
  if (item.item_type === "paper") return item.why_it_matters ?? null;
  return item.market_impact ?? null;
}

function reliabilityClass(reliability?: string | null): string | null {
  if (!reliability) return null;
  if (reliability === "High") return "tagReliabilityHigh";
  if (reliability === "Medium") return "tagReliabilityMedium";
  if (reliability === "Low") return "tagReliabilityLow";
  return null;
}

function ItemCard({ item, showSectionTag }: { item: ItemOut; showSectionTag?: boolean }) {
  const why = cardWhyText(item);
  const score = Math.round((item.rank_score ?? 0) * 100);
  const relClass = reliabilityClass(item.source_reliability);

  return (
    <div className="card" key={item.id}>
      <div className="cardTitle">
        <a href={item.source_url} target="_blank" rel="noreferrer">
          {item.title}
        </a>
      </div>
      <div className="metaRow">
        {score >= 90 ? <span className="tag tagStrong">Top</span> : null}
        <span className="tag tagStrong">{item.item_type === "paper" ? "Research" : "Industry"}</span>
        {showSectionTag ? <span className="tag">{sectionLabel(item.section)}</span> : null}
        <span className="tag">{item.source}</span>
        <span className="tag">Published: {prettyUtc(item.published_at_utc)}</span>
        <span className="tag">Score: {score}</span>
        {item.difficulty ? <span className="tag">Difficulty: {item.difficulty}</span> : null}
        {item.source_reliability ? (
          <span className={`tag ${relClass ?? ""}`.trim()}>Reliability: {item.source_reliability}</span>
        ) : null}
        {item.tags.slice(0, 6).map((t) => (
          <span className="tag" key={t}>
            {t}
          </span>
        ))}
      </div>
      <ul className="bullets">
        {item.summary_bullets.slice(0, item.item_type === "paper" ? 5 : 4).map((b, idx) => (
          <li key={idx}>{b}</li>
        ))}
      </ul>
      {why ? (
        <div className="why">
          <span className="whyLabel">{cardWhyLabel(item)}</span>
          {why}
        </div>
      ) : null}
    </div>
  );
}

function SectionBlock({ section, items }: { section: Section; items: ItemOut[] }) {
  return (
    <div className="section">
      <div className="sectionHeader">
        <div className="sectionName">{sectionLabel(section)}</div>
        <div className="sectionMeta">{items.length} items</div>
      </div>
      <div className="cards">
        {items.length === 0 ? (
          <div className="card">
            <div className="metaRow">No items yet for this edition.</div>
          </div>
        ) : (
          items.map((item) => <ItemCard key={item.id} item={item} />)
        )}
      </div>
    </div>
  );
}

export function Dashboard() {
  const [tz, setTz] = useState<string>("Asia/Hong_Kong");
  const [query, setQuery] = useState<string>("");
  const [editions, setEditions] = useState<EditionMetaOut[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [edition, setEdition] = useState<EditionOut | null>(null);
  const [activeSection, setActiveSection] = useState<Section>("ai_for_science");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let canceled = false;
    setError(null);
    setEditions(null);
    setEdition(null);
    setSelected(null);
    fetchEditions(tz)
      .then((e) => {
        if (canceled) return;
        setEditions(e);
        setSelected(e[0]?.edition_date_local ?? null);
      })
      .catch((err) => {
        if (canceled) return;
        setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      canceled = true;
    };
  }, [tz]);

  useEffect(() => {
    if (!selected) return;
    let canceled = false;
    setError(null);
    setEdition(null);
    fetchEdition(tz, selected)
      .then((e) => {
        if (canceled) return;
        setEdition(e);
      })
      .catch((err) => {
        if (canceled) return;
        setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      canceled = true;
    };
  }, [tz, selected]);

  useEffect(() => {
    if (!edition) return;
    if (ALL_SECTIONS.includes(activeSection)) return;
    setActiveSection("ai_for_science");
  }, [edition, activeSection]);

  const selectedMeta = useMemo(() => editions?.find((e) => e.edition_date_local === selected) ?? null, [editions, selected]);

  const filterFn = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return (i: ItemOut) => true;
    return (i: ItemOut) => {
      if (i.title.toLowerCase().includes(q)) return true;
      if (i.source.toLowerCase().includes(q)) return true;
      return i.tags.some((t) => t.toLowerCase().includes(q));
    };
  }, [query]);

  const sectionItems = useMemo(() => {
    if (!edition) return [];
    return (edition.sections[activeSection] ?? []).filter(filterFn);
  }, [edition, activeSection, filterFn]);

  const searchItems = useMemo(() => {
    if (!edition) return [];
    const q = query.trim();
    if (!q) return [];
    const all = ALL_SECTIONS.flatMap((s) => edition.sections[s] ?? []);
    const filtered = all.filter(filterFn);
    filtered.sort((a, b) => new Date(b.published_at_utc).getTime() - new Date(a.published_at_utc).getTime());
    return filtered;
  }, [edition, query, filterFn]);

  const subtitle = selectedMeta
    ? `Edition date: ${prettyLocalLabel(selectedMeta.edition_date_local)} (summarizes UTC ${selectedMeta.utc_date})`
    : "Daily edition (summarizes the previous UTC day).";

  return (
    <div className="container">
      <div className="header">
        <div className="brand">
          <div className="title">Nexus AI Daily</div>
          <div className="subtitle">{subtitle}</div>
        </div>
        <div className="controls">
          <input
            className="input"
            placeholder="Filters: keyword or tag…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select className="select" value={tz} onChange={(e) => setTz(e.target.value)}>
            {TZ_PRESETS.map((z) => (
              <option key={z} value={z}>
                {z}
              </option>
            ))}
          </select>
          <div className="pill">Recent 7 Days</div>
        </div>
      </div>

      <div className="tabs" aria-label="day tabs">
        {(editions ?? []).map((e, idx) => {
          const label = idx === 0 ? `Today · ${prettyLocalLabel(e.edition_date_local)}` : prettyLocalLabel(e.edition_date_local);
          const active = selected === e.edition_date_local;
          return (
            <button
              key={e.edition_date_local}
              className={`tab ${active ? "tabActive" : ""}`}
              onClick={() => setSelected(e.edition_date_local)}
            >
              {label}
            </button>
          );
        })}
        {!editions ? <div className="pill">Loading…</div> : null}
      </div>

      {error ? <div className="pill">Error: {error}</div> : null}

      <div className="sectionNav">
        {ALL_SECTIONS.map((s) => {
          const active = s === activeSection;
          return (
            <button
              key={s}
              className={`navBtn ${active ? "navBtnActive" : ""}`}
              onClick={() => setActiveSection(s)}
              disabled={query.trim().length > 0}
              title={query.trim().length > 0 ? "Clear search to browse by section" : undefined}
            >
              {sectionLabel(s)}
            </button>
          );
        })}
      </div>

      {query.trim() ? (
        <div className="hub">
          <div className="hubTitle">SEARCH RESULTS</div>
          <div className="section">
            <div className="sectionHeader">
              <div className="sectionName">Matches (latest → oldest)</div>
              <div className="sectionMeta">{searchItems.length} items</div>
            </div>
            <div className="cards">
              {searchItems.length === 0 ? (
                <div className="card">
                  <div className="metaRow">No matches for this edition.</div>
                </div>
              ) : (
                searchItems.map((item) => <ItemCard key={item.id} item={item} showSectionTag />)
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="hub">
          <div className="hubTitle">SECTION</div>
          <SectionBlock section={activeSection} items={sectionItems} />
        </div>
      )}

      <div className="footer">
        <div className="footerLinks">
          <span className="buttonLink">Customize</span>
          <span className="buttonLink">Email Digest</span>
          <span className="buttonLink">Export Slides</span>
        </div>
        <div className="footerLinks">
          <span>
            Semantics: tab date X summarizes previous UTC day (X-1).
          </span>
        </div>
      </div>
    </div>
  );
}
