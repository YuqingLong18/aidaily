'use client';

import React from 'react';
import { Item } from '@prisma/client';

interface NewsCardProps {
  item: Item;
  language: 'en' | 'zh';
  dateFormatter?: Intl.DateTimeFormat;
}

function toBullets(raw?: string) {
  if (!raw) return [];
  return raw
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
    .map(line => line.replace(/^-+\s*/, '').trim());
}

function toKeywords(raw?: string) {
  if (!raw) return [];
  return raw
    .split(',')
    .map(k => k.trim())
    .filter(Boolean);
}

function extractWhy(raw?: string) {
  if (!raw) return '';
  const match = raw.split(/why it matters[:\-\u2014]*/i);
  if (match.length > 1) {
    return match.slice(1).join(' ').replace(/^\*\*|\*\*$/g, '').trim();
  }
  return '';
}

export function NewsCard({ item, language, dateFormatter }: NewsCardProps) {
  const isAcademic = item.type === 'academic';
  const hasImage = Boolean(item.imageUrl);
  const imageAlt = item.imageAlt || item.title;
  const locale = language === 'zh' ? 'zh-CN' : 'en-US';
  const summaryText =
    language === 'zh'
      ? item.summaryZh || item.summaryEn || item.summary
      : item.summaryEn || item.summary || item.summaryZh;
  const whyTextRaw =
    language === 'zh'
      ? item.whyItMattersZh || item.whyItMattersEn || extractWhy(item.summaryZh || item.summary)
      : item.whyItMattersEn || item.whyItMattersZh || extractWhy(item.summaryEn || item.summary);
  const keywordsText = language === 'zh' ? item.keywordsZh || item.keywordsEn : item.keywordsEn || item.keywordsZh;

  const bullets = toBullets(summaryText);
  const keywords = toKeywords(keywordsText);
  const publishedDate = new Date(item.publishedAt);
  const formattedDate = (
    dateFormatter ||
    new Intl.DateTimeFormat(locale, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      timeZone: 'UTC',
    })
  ).format(publishedDate);

  const labelWhy = language === 'zh' ? '价值要点' : 'Why it matters';
  const labelSource = language === 'zh' ? '来源' : 'Source';
  const labelScore = language === 'zh' ? '评分' : 'Score';

  return (
    <div
      className={`p-5 rounded-xl border ${
        isAcademic ? 'border-blue-200 bg-blue-50/70' : 'border-green-200 bg-green-50/70'
      } hover:shadow-md transition-shadow`}
    >
      <div className="flex justify-between items-start mb-3">
        <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-500">
          {item.category}
        </span>
        <span className="text-xs text-gray-400">{formattedDate}</span>
      </div>

      <h3 className="text-xl font-extrabold mb-3 leading-snug text-gray-900">
        <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:underline text-gray-900">
          {item.title}
        </a>
      </h3>

      {hasImage && (
        <div className="mb-4 overflow-hidden rounded-lg border border-white/70 bg-white shadow-sm">
          <img src={item.imageUrl!} alt={imageAlt} className="h-48 w-full object-cover" loading="lazy" />
        </div>
      )}

      {keywords.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {keywords.map((kw, idx) => (
            <span
              key={idx}
              className={`rounded-full px-3 py-1 text-base font-semibold ${
                isAcademic ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
              }`}
            >
              {kw}
            </span>
          ))}
        </div>
      )}

      {bullets.length > 0 && (
        <ul className="text-sm text-gray-800 mb-4 space-y-2">
          {bullets.map((point, idx) => (
            <li key={idx} className="flex gap-3">
              <span className={`mt-2 h-2 w-2 rounded-full ${isAcademic ? 'bg-blue-400' : 'bg-green-400'}`} />
              <span className="leading-relaxed">{point}</span>
            </li>
          ))}
        </ul>
      )}

      {whyTextRaw && (
        <div className="mt-2 rounded-lg border border-dashed border-gray-200 bg-white/70 px-4 py-3">
          <p
            className={`text-[11px] font-semibold uppercase tracking-[0.1em] mb-1 ${
              isAcademic ? 'text-blue-700' : 'text-green-700'
            }`}
          >
            {labelWhy}
          </p>
          <p className="text-sm text-gray-800 leading-relaxed">{whyTextRaw}</p>
        </div>
      )}

      <div className="flex justify-between items-center mt-4">
        <span className="text-xs font-medium text-gray-500">
          {labelSource}: {item.source}
        </span>
        <span className="text-xs font-bold text-gray-600">
          {labelScore}: <span className="text-xs font-extrabold text-indigo-600">{item.score.toFixed(1)}</span>
        </span>
      </div>
    </div>
  );
}
