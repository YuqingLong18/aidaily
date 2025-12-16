# Product Requirements Document (PRD)
**Product Name (working):** Nexus AI Daily  
**Document Version:** v1.0  
**Last Updated:** 2025-12-10  
**Owner:** [User Name]  

---

## 1. Product Overview

### Vision  
Nexus AI Daily delivers a daily, high-quality intelligence dashboard that distills the most impactful AI research, product releases, and ecosystem developments. It is designed for researchers, educators, and innovators who need fast, actionable intelligence.

### Value Proposition
- Reduce cognitive overload by filtering thousands of new AI papers/news daily.
- Translate research breakthroughs into teaching and product implications.
- Provide structured summaries and insights to support quick decision-making.
- Deliver a reliable daily habit that takes <10 minutes to consume.

---

## 2. Goals & Success Metrics

| Category | Metric | Target (Phase 1) |
|---------|--------|-----------------|
| Engagement | Daily Active Users (DAU) | 200+ private beta |
| Utility | Avg. session duration | 4–10 minutes |
| Quality | User-rated “useful” score | >70% |
| Growth | Email digest subscribers | 500+ |
| Accuracy | Hallucination reports per 100 items | <2 |

---

## 3. Scope

### In Scope (MVP)
- Academic and industry intelligence split into 5 curated sections.
- Daily ingestion (papers + web/RSS sources).
- Ranking + topic classification.
- LLM-driven structured summarization.
- Web dashboard (desktop-first).
- Email digest with same content.
- User accounts and interest-based personalization.

### Out of Scope (Phase 1)
- Real-time monitoring or breaking alerts.
- Collaborative annotation/social features.
- Mobile-native apps.
- Multi-language support.
- Advanced personalization using ML models.

---

## 4. Product Experience

### Daily Dashboard Structure
Header: Date • Summary • Filters
───────────────────────────────
ACADEMIC INTELLIGENCE HUB
AI for Science (Top 5)
AI Theory & Architectures (Top 5)
AI in Education (Top 5)
───────────────────────────────
INDUSTRY INTELLIGENCE HUB
Product & Technology Watch (Top 3–6)
Market & Policy Lens (Top 3–5)
───────────────────────────────
Footer: Customize • Email Digest • Export Slides
### Item Card Format

**Research Paper Card**
- Title (link)
- Tags; Difficulty level
- 3–5 bullet summary of key ideas
- 1 bullet on “Why it matters”
- Source (arXiv, etc.)

**Industry News Card**
- Company + product or event type
- 2–4 bullet summary
- 1 bullet market/impact analysis
- Source reliability indicator

### Detail View
- Full structured summary
- Source quote or figure if available
- Related article recommendations
- Educator Mode:
  - Simplified explanation
  - Classroom prompts (2–3)
  - Ethics/access considerations

---
## Date & Time Semantics (Critical)

### User-facing day tabs (Local Display)
- The dashboard displays **7 day-tabs**: **Today, Today-1, …, Today-6**.
- Tabs are labeled using the user’s **local calendar dates** (e.g., in Hong Kong time, `16 Dec` down to `10 Dec`).

### Content window per tab (UTC-based “yesterday” model)
Each displayed day **X (local date label)** shows the **content published during the previous UTC day (X-1 in UTC)**.

Rationale:
- The dashboard is intended as a **morning summary**.
- If the ingestion runs at **08:00 Hong Kong time** on `16 Dec`, there is typically little content published on `16 Dec` yet (local time).
- However, **UTC `15 Dec` has completed**, so the system summarizes the fully closed day in UTC.

### Formal Definition
Let:
- `X` = a local date shown as a tab (e.g., `2025-12-16` in Asia/Hong_Kong)
- `UTC_day(X-1)` = the UTC date one day before `X` (e.g., `2025-12-15`)

Then:
- Tab `X` shows items with `published_at_utc` in:
  - `UTC_day(X-1) 00:00:00` to `UTC_day(X-1) 23:59:59` (inclusive)

### Example (HK time)
- Ingestion runs: `2025-12-16 08:00` (Asia/Hong_Kong)
- The edition labeled: `16 Dec`
- It includes content published in UTC:
  - `2025-12-15 00:00` → `2025-12-15 23:59:59`

### Recent 7 Days Button
- Clicking **Recent 7 Days** shows day tabs for:
  - `X = Today_local` down to `Today_local - 6 days`
- Each tab `X` maps to the UTC window for `X-1`.

### Data Model Requirements (timestamps)
Store and compute with explicit timestamps:
- `published_at_utc` (required) — normalized publication time in UTC
- `edition_date_local` (required) — the local date label `X` under which the item is displayed
- `edition_timezone` (required) — user-configurable, default `Asia/Hong_Kong`

### Ingestion & Idempotency Requirements
- The ingestion service runs once daily (default `08:00 Asia/Hong_Kong`).
- For each run at local date `X`, it generates/updates the edition for `X` by querying the UTC window of `X-1`.
- Runs must be **idempotent**:
  - Re-running ingestion for `X` should not duplicate items.
  - Deduplication key suggestions:
    - `source_url` (preferred), or
    - (`source`, `external_id`) if available, else
    - hash of (`title`, `canonical_url`, `published_at_utc`)

### Edge Cases & Notes
- If a source provides only a date (no time), assume `published_at_utc = UTC_day(X-1) 12:00` and mark `timestamp_precision = "date_only"`.
- If publication timestamp is in local time or unknown timezone:
  - Convert using source-provided timezone if available;
  - Otherwise attempt reliable parsing; if uncertain, mark `timestamp_confidence = "low"` and allow inclusion only if the local date clearly maps into the UTC window.
- The UI should disclose the semantics:
  - “Edition date: 16 Dec (summarizes UTC 15 Dec)”
---

## 6. Data & Content Pipeline

### Source Coverage

Academic:
- arXiv API (cs.LG, cs.AI, cs.CL, cs.CV, stat.ML)
- Semantic Scholar metadata (optional)

Industry:
- Major AI company blogs (OpenAI, Google, Meta, Anthropic, robotics companies)
- Selected tech and business RSS feeds
- Curated trusted newsletters (pending licensing)

### Processing Pipeline

1. Ingestion  
   - Scheduled cron job (daily 03:00–05:00 UTC)  
   - Normalize metadata into common schema  

2. Classification  
   - Academic categories:
     - AI for Science (AIFS)
     - AI Theory & Architectures
     - AI in Education  
   - Industry categories:
     - Product & Technology
     - Market & Policy

3. Ranking  
   - Academic score: recency + topic relevance + institution signals + diversity  
   - Industry score: market reach + funding significance + policy relevance

4. Summarization  
   - Automated LLM structured templates
   - Confidence check to flag questionable AI claims

5. Storage  
   - PostgreSQL for content and user data  
   - Redis cache for daily edition performance

6. Delivery  
   - REST API for dashboard  
   - Email digest generation from same data

---

## 7. System Architecture

| Layer | Component | Technology |
|------|-----------|------------|
| Data ingestion | Ingestion service | Python scripts / FastAPI |
| Processing | Classifier + ranker + summarizer | Hosted LLM APIs |
| Backend API | Content & auth services | FastAPI / Node |
| Frontend | Dashboard | Next.js / React |
| Storage | Item DB | PostgreSQL |
| Cache | Hot cache | Redis |
| Identity | Auth | OAuth / JWT |

Requirements:
- HTTPS everywhere, secure key storage
- Store minimal personal data

---

## 8. Non-Functional Requirements

| Category | Requirement |
|--------|-------------|
| Performance | Dashboard loads in <1.5s after cache warm |
| Reliability | Successful daily edition generation |
| Availability | >99% uptime |
| Scalability | Support 10k DAU |
| Compliance | Respect robots.txt and data source TOS |
| Privacy | No unnecessary tracking or profiling |

---

## 9. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucinations | Reduced trust | Fact validation + quotes |
| API or scraping failures | Missing content | Redundant sources + alerting |
| High LLM cost | Budget impact | Batch jobs + caching + model tiering |
| Poor differentiation | Low engagement | Educator Mode + academic structuring |
| Quality variance | Misleading signals | Human curation for top trends if needed |

---

## 10. Roadmap

| Phase | Timeline | Deliverables |
|------|----------|--------------|
| 0 – Prototype | Month 1 | Manual curation, static UI |
| 1 – MVP | Month 2–3 | Full pipeline, 5 sections, personalization, email digest |
| 2 – Educator Mode | Month 4–6 | Export to slides, classroom view |
| 3 – Smart Insights | Month 6–9 | Trend analytics, better personalization |
| 4 – Expansion | Month 9+ | Mobile app, team workflows, multilingual |

---

## 11. Open Questions

- Are any sources subject to commercial licensing requirements?
- Should top items receive human editorial review?
- Add evaluation leaderboards or replicability markers?
- Support user feedback on item-level usefulness?

---

## Summary

Nexus AI Daily provides:
- A curated AI intelligence dashboard across science, theory, education, products, and policy.
- Structured insights designed for rapid digestion and real-world impact.
- A foundation for growth into a leading AI literacy and research intelligence platform.